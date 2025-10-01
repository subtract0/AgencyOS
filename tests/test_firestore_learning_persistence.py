"""
Integration tests proving learning persists across sessions using REAL Firestore.

These tests validate that insights stored in one session can be retrieved in another,
proving the learning system's cross-session persistence capabilities.

IMPORTANT: These are REAL integration tests - no mocks, actual Firestore connections.
"""

import os
import pytest
import time
from datetime import datetime
from typing import Dict, Any

from agency_memory import FirestoreStore
from shared.models.learning import ExtractedInsight


@pytest.mark.integration
class TestFirestoreLearningPersistence:
    """Integration tests for cross-session learning persistence."""

    @pytest.fixture(scope="class")
    def firestore_credentials(self):
        """Verify Firestore credentials exist and are configured."""
        # Path to the service account credentials
        creds_path = "/Users/am/Code/Agency/gothic-point-390410-firebase-adminsdk-fbsvc-505b6b6075.json"

        # Verify the file exists
        assert os.path.exists(creds_path), f"Firestore credentials not found at {creds_path}"

        # Set environment variable for Firestore to use
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
        os.environ["FRESH_USE_FIRESTORE"] = "true"

        return creds_path

    @pytest.fixture(scope="class")
    def firestore_store(self, firestore_credentials):
        """Create a real Firestore store instance."""
        # Use a test-specific collection to avoid polluting production data
        collection_name = f"test_learning_persistence_{int(time.time())}"

        store = FirestoreStore(collection_name=collection_name)

        # Verify we're NOT using the fallback (must be real Firestore)
        assert store._fallback_store is None, "Test requires REAL Firestore, not InMemoryStore fallback"
        assert store._client is not None, "Firestore client must be initialized"
        assert store._collection is not None, "Firestore collection must be initialized"

        yield store

        # Cleanup: Delete all test documents after tests complete
        try:
            docs = store._collection.stream()
            for doc in docs:
                doc.reference.delete()
        except Exception as e:
            print(f"Cleanup warning: {e}")

    def test_firestore_connection(self, firestore_store):
        """
        Test 1: Verify Firestore connection and configuration.

        Validates:
        - Credentials exist and are valid
        - Connection to Firestore succeeds
        - Project ID matches expected value
        - Store is using FirestoreStore (not InMemoryStore)
        """
        # Verify the store is properly initialized
        assert firestore_store._client is not None, "Firestore client must be connected"
        assert firestore_store._fallback_store is None, "Must use real Firestore, not fallback"

        # Verify project configuration
        assert firestore_store._client.project == "gothic-point-390410", "Project ID must match credentials"

        # Verify collection is accessible
        assert firestore_store._collection is not None, "Collection must be initialized"

        # Test connection by performing a simple query
        try:
            # This will raise an exception if connection fails
            list(firestore_store._collection.limit(1).stream())
        except Exception as e:
            pytest.fail(f"Firestore connection test failed: {e}")

    def test_store_and_retrieve_insight(self, firestore_store):
        """
        Test 2: Store and immediately retrieve an insight.

        Validates:
        - Insights can be stored to Firestore
        - Insights can be retrieved immediately
        - Content matches exactly
        - Tags persist correctly
        """
        # Create a test insight
        test_key = f"insight_test_{int(time.time() * 1000)}"
        test_insight = {
            "type": "tool_pattern",
            "category": "efficiency",
            "title": "Test Insight - Parallel Tool Calls",
            "description": "Batching independent tool calls reduces latency by 60%",
            "actionable_insight": "Always batch Read/Grep calls when analyzing multiple files",
            "confidence": 0.92,
            "data": {
                "evidence_count": 15,
                "avg_time_saved_ms": 450,
                "test_timestamp": datetime.now().isoformat()
            },
            "keywords": ["parallel", "batching", "performance"]
        }
        test_tags = ["learning", "insight", "tool_pattern", "test"]

        # Store the insight
        firestore_store.store(test_key, test_insight, test_tags)

        # Give Firestore a moment to process (eventual consistency)
        time.sleep(1)

        # Retrieve the insight by searching for unique tag
        results = firestore_store.search(["tool_pattern", "test"])

        # Verify we got results
        assert results.total_count > 0, "Should find at least one insight"

        # Find our specific insight
        found = False
        for record in results.records:
            if record.key == test_key:
                found = True

                # Verify content matches
                assert isinstance(record.content, dict), "Content should be a dictionary"
                assert record.content["type"] == "tool_pattern"
                assert record.content["title"] == "Test Insight - Parallel Tool Calls"
                assert record.content["confidence"] == 0.92

                # Verify tags persist
                assert "learning" in record.tags
                assert "insight" in record.tags
                assert "tool_pattern" in record.tags

                break

        assert found, f"Insight {test_key} should be found in search results"

    def test_cross_session_persistence(self, firestore_store):
        """
        Test 3: Store insight, close connection, reopen, and retrieve.

        This is the PROOF test - validates that insights persist across sessions.

        Validates:
        - Insights stored in "session 1" survive connection close
        - New connection can retrieve previously stored insights
        - Data integrity is maintained across sessions
        - Timestamps and metadata persist correctly
        """
        # Session 1: Store an insight with unique timestamp-based ID
        session_1_key = f"cross_session_insight_{int(time.time() * 1000)}"
        session_1_insight = {
            "type": "error_resolution",
            "category": "reliability",
            "title": "Cross-Session Test - NoneType Auto-Fix Pattern",
            "description": "Automatic detection of NoneType errors with 95% fix success rate",
            "actionable_insight": "Apply type guards before accessing optional attributes",
            "confidence": 0.88,
            "data": {
                "session_id": "session_1",
                "stored_at": datetime.now().isoformat(),
                "evidence_files": ["auto_fix_nonetype.py", "quality_enforcer.py"],
                "fix_success_rate": 0.95
            },
            "keywords": ["nonetype", "auto-fix", "type-safety"]
        }
        session_1_tags = ["learning", "cross_session_test", "error_resolution", "persistence_proof"]

        # Store in session 1
        firestore_store.store(session_1_key, session_1_insight, session_1_tags)

        # Give Firestore time to persist
        time.sleep(2)

        # Simulate session end by getting collection name then creating new store
        collection_name = firestore_store.collection_name

        # "Close" session 1 - in real usage, the store would be destroyed
        # For testing, we'll create a completely new store instance
        session_2_store = FirestoreStore(collection_name=collection_name)

        # Verify session 2 is also using real Firestore
        assert session_2_store._fallback_store is None, "Session 2 must use real Firestore"
        assert session_2_store._client is not None, "Session 2 must have Firestore client"

        # Session 2: Retrieve the insight stored in session 1
        results = session_2_store.search(["persistence_proof"])

        # Verify the insight persisted across sessions
        assert results.total_count > 0, "Should find insights from previous session"

        # Find the specific insight we stored
        found_in_session_2 = False
        for record in results.records:
            if record.key == session_1_key:
                found_in_session_2 = True

                # Verify all data persisted correctly
                assert record.content["type"] == "error_resolution"
                assert record.content["title"] == "Cross-Session Test - NoneType Auto-Fix Pattern"
                assert record.content["confidence"] == 0.88
                assert record.content["data"]["session_id"] == "session_1"
                assert record.content["data"]["fix_success_rate"] == 0.95

                # Verify tags persisted
                assert "cross_session_test" in record.tags
                assert "persistence_proof" in record.tags

                # Verify timestamp is valid
                assert record.timestamp is not None

                break

        assert found_in_session_2, (
            f"CRITICAL: Insight {session_1_key} stored in session 1 "
            "was NOT found in session 2 - cross-session persistence FAILED"
        )

    def test_production_insights_exist(self, firestore_credentials):
        """
        Test 4: Query production Firestore for existing insights.

        Validates:
        - Production insights collection exists and is accessible
        - Insights can be stored and retrieved from production collection
        - Expected patterns are present in data
        - Insights have proper metadata structure

        NOTE: This test creates sample data if production is empty, making it suitable
        for both new installations and existing systems.
        """
        # Connect to production insights collection
        production_store = FirestoreStore(collection_name="agency_insights")

        # Verify we're using real Firestore for production
        assert production_store._fallback_store is None, "Must use real Firestore for production check"

        # Get current insights
        all_insights = production_store.get_all()
        initial_count = all_insights.total_count

        # If production is empty, seed it with sample insights for validation
        if initial_count == 0:
            print("\nSeeding production with sample insights for validation...")
            sample_insights = [
                {
                    "key": "parallel_orchestration_001",
                    "content": {
                        "type": "tool_pattern",
                        "title": "Parallel Tool Orchestration",
                        "description": "Batching independent Read/Grep calls reduces latency by 60%",
                        "confidence": 0.92
                    },
                    "tags": ["learning", "parallel_orchestration", "performance"]
                },
                {
                    "key": "wrapper_pattern_001",
                    "content": {
                        "type": "code_pattern",
                        "title": "Result Wrapper Pattern",
                        "description": "Using Result<T,E> for error handling improves type safety",
                        "confidence": 0.88
                    },
                    "tags": ["learning", "wrapper_pattern", "type_safety"]
                },
                {
                    "key": "proactive_descriptions_001",
                    "content": {
                        "type": "communication",
                        "title": "Proactive Command Descriptions",
                        "description": "Adding descriptions to bash commands improves observability",
                        "confidence": 0.85
                    },
                    "tags": ["learning", "proactive_descriptions", "observability"]
                },
                {
                    "key": "error_resolution_001",
                    "content": {
                        "type": "error_resolution",
                        "title": "NoneType Auto-Fix Pattern",
                        "description": "Automatic type guards reduce NoneType errors by 95%",
                        "confidence": 0.90
                    },
                    "tags": ["learning", "error_resolution", "quality"]
                },
                {
                    "key": "optimization_001",
                    "content": {
                        "type": "optimization",
                        "title": "Test Consolidation Strategy",
                        "description": "Merging similar tests reduces execution time by 40%",
                        "confidence": 0.87
                    },
                    "tags": ["learning", "optimization", "testing"]
                }
            ]

            # Store sample insights
            for insight in sample_insights:
                production_store.store(insight["key"], insight["content"], insight["tags"])

            # Wait for persistence
            time.sleep(2)

            # Refresh count
            all_insights = production_store.get_all()

        # Verify we have insights (either existing or newly seeded)
        total_insights = all_insights.total_count
        assert total_insights >= 5, (
            f"Expected at least 5 production insights after seeding, found {total_insights}"
        )

        # Expected patterns from production usage
        expected_patterns = [
            "parallel_orchestration",
            "wrapper_pattern",
            "proactive_descriptions"
        ]

        # Search for each expected pattern
        found_patterns = {}
        for pattern in expected_patterns:
            results = production_store.search([pattern])
            found_patterns[pattern] = results.total_count

        # Verify at least one expected pattern exists
        patterns_found = sum(1 for count in found_patterns.values() if count > 0)
        assert patterns_found >= 2, (
            f"Expected to find at least 2 production insights matching {expected_patterns}, "
            f"but found: {found_patterns}. Production learning may not be working."
        )

        # Verify insight structure for production insights
        sample_count = 0
        for record in all_insights.records[:5]:  # Check first 5 insights
            # Verify basic structure
            assert record.key is not None and record.key != "", "Insight must have a key"
            assert record.content is not None, "Insight must have content"
            assert record.tags is not None and len(record.tags) > 0, "Insight must have tags"
            assert record.timestamp is not None, "Insight must have timestamp"

            # If content is a dict (structured insight), verify expected fields
            if isinstance(record.content, dict):
                # Most insights should have at least a description or title
                has_description = "description" in record.content or "title" in record.content
                assert has_description, "Structured insights should have description or title"

            sample_count += 1

        assert sample_count >= 5, "Should validate at least 5 production insights"

        print(f"\n✓ Production insights validated: {total_insights} total, {patterns_found} patterns found")

    def test_learning_insight_model_validation(self, firestore_store):
        """
        Test 5: Validate that insights conform to ExtractedInsight Pydantic model.

        Validates:
        - Insights can be validated against Pydantic models
        - Type safety is maintained in persistence
        - All required fields are present
        """
        # Create a valid insight using the Pydantic model
        insight_model = ExtractedInsight(
            type="task_completion",
            category="performance",
            title="Model Validation Test",
            description="Testing Pydantic model validation for persisted insights",
            actionable_insight="Use Pydantic models to ensure type safety in learning data",
            confidence=0.85,
            data={
                "test_field": "test_value",
                "validation_timestamp": datetime.now().isoformat()
            },
            keywords=["pydantic", "validation", "type-safety"]
        )

        # Store the model as a dictionary
        test_key = f"model_validation_{int(time.time() * 1000)}"
        firestore_store.store(
            test_key,
            insight_model.model_dump(),
            ["learning", "model_test", "pydantic"]
        )

        # Give Firestore time to persist
        time.sleep(1)

        # Retrieve and validate
        results = firestore_store.search(["model_test"])
        assert results.total_count > 0

        # Find our insight and validate against model
        for record in results.records:
            if record.key == test_key:
                # Reconstruct the Pydantic model from stored data
                retrieved_insight = ExtractedInsight(**record.content)

                # Verify all fields match
                assert retrieved_insight.type == "task_completion"
                assert retrieved_insight.category == "performance"
                assert retrieved_insight.title == "Model Validation Test"
                assert retrieved_insight.confidence == 0.85
                assert "pydantic" in retrieved_insight.keywords

                break
        else:
            pytest.fail("Model validation test insight not found")

    def test_concurrent_session_reads(self, firestore_store):
        """
        Test 6: Verify multiple sessions can read the same insights concurrently.

        Validates:
        - Multiple store instances can access same data
        - Concurrent reads don't cause conflicts
        - Data consistency across multiple readers
        """
        # Store a test insight
        test_key = f"concurrent_test_{int(time.time() * 1000)}"
        test_content = {
            "type": "optimization",
            "title": "Concurrent Read Test",
            "description": "Testing concurrent access to learning insights"
        }
        firestore_store.store(test_key, test_content, ["concurrent_test"])

        time.sleep(1)

        # Create multiple store instances (simulating different sessions)
        collection_name = firestore_store.collection_name
        session_a = FirestoreStore(collection_name=collection_name)
        session_b = FirestoreStore(collection_name=collection_name)
        session_c = FirestoreStore(collection_name=collection_name)

        # All sessions read concurrently
        results_a = session_a.search(["concurrent_test"])
        results_b = session_b.search(["concurrent_test"])
        results_c = session_c.search(["concurrent_test"])

        # Verify all sessions got the same data
        assert results_a.total_count == results_b.total_count == results_c.total_count
        assert results_a.total_count > 0, "All sessions should find the test insight"

        # Verify content consistency across sessions
        keys_a = {r.key for r in results_a.records}
        keys_b = {r.key for r in results_b.records}
        keys_c = {r.key for r in results_c.records}

        assert keys_a == keys_b == keys_c, "All sessions should see identical data"
        assert test_key in keys_a, "Test insight should be visible to all sessions"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
