"""
Integration tests for external services.

This test suite contains real integration tests that interact with external services
when the appropriate environment variables are configured. These tests are marked
with @pytest.mark.integration and skip automatically if required environment
variables are not set.

Tests include:
- Firestore integration with emulator
- OpenAI API integration with minimal cost operations
"""

import os
import pytest
import time
from datetime import datetime

# CI skip marker for tests requiring external API keys
ci_skip = pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Requires external API keys not available in CI"
)

# Test OpenAI integration only if available
try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Test Firestore integration only if available
try:
    from google.cloud import firestore

    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False

from agency_memory import FirestoreStore


@pytest.mark.integration
class TestFirestoreIntegration:
    """Integration tests for Firestore with emulator."""

    @pytest.fixture
    def firestore_client(self):
        """Create a Firestore client for testing with emulator."""
        # Skip if Firestore not enabled or emulator not configured
        if not os.getenv("FRESH_USE_FIRESTORE", "").lower() == "true":
            pytest.skip("FRESH_USE_FIRESTORE not set to 'true'")

        if not os.getenv("FIRESTORE_EMULATOR_HOST"):
            pytest.skip("FIRESTORE_EMULATOR_HOST not configured")

        if not FIRESTORE_AVAILABLE:
            pytest.skip("google-cloud-firestore not available")

        # Set project for emulator
        os.environ["GOOGLE_CLOUD_PROJECT"] = "agency-test"
        client = firestore.Client()

        yield client

        # Cleanup: Delete test collection after each test
        try:
            collection_ref = client.collection("test_integration_memories")
            docs = collection_ref.stream()
            for doc in docs:
                doc.reference.delete()
        except Exception:
            pass  # Ignore cleanup errors

    def test_firestore_crud_operations(self, firestore_client):
        """Test complete CRUD operations with Firestore emulator."""
        collection_name = "test_integration_memories"
        test_key = f"integration_test_{int(time.time())}"
        test_content = "Integration test content"
        test_tags = ["integration", "test", "firestore"]

        # Create a FirestoreStore instance
        store = FirestoreStore(collection_name)

        # Verify Firestore is actually being used (not fallback)
        assert store._client is not None, (
            "FirestoreStore should use real Firestore client"
        )
        assert store._fallback_store is None, "FirestoreStore should not use fallback"

        # Test CREATE operation
        store.store(test_key, test_content, test_tags)

        # Verify data was written to Firestore
        doc_ref = firestore_client.collection(collection_name).document(test_key)
        doc = doc_ref.get()
        assert doc.exists, "Document should exist in Firestore"

        doc_data = doc.to_dict()
        assert doc_data["key"] == test_key
        assert doc_data["content"] == test_content
        assert doc_data["tags"] == test_tags
        assert "timestamp" in doc_data

        # Test READ operation via search
        search_results = store.search(["integration"])
        assert len(search_results) >= 1, (
            "Should find at least one integration test record"
        )

        found_record = None
        for record in search_results:
            if record["key"] == test_key:
                found_record = record
                break

        assert found_record is not None, "Should find the test record"
        assert found_record["content"] == test_content
        assert set(found_record["tags"]) == set(test_tags)

        # Test READ operation via get_all
        all_memories = store.get_all()
        assert len(all_memories) >= 1, "Should retrieve at least one memory"

        found_in_all = any(m["key"] == test_key for m in all_memories)
        assert found_in_all, "Test record should be found in get_all results"

        # Test UPDATE operation (store with same key)
        updated_content = "Updated integration test content"
        updated_tags = ["integration", "test", "firestore", "updated"]
        store.store(test_key, updated_content, updated_tags)

        # Verify update
        updated_doc = doc_ref.get()
        updated_data = updated_doc.to_dict()
        assert updated_data["content"] == updated_content
        assert updated_data["tags"] == updated_tags

        # Test DELETE operation
        doc_ref.delete()

        # Verify deletion
        deleted_doc = doc_ref.get()
        assert not deleted_doc.exists, "Document should be deleted"

        # Verify deletion affects search results
        search_after_delete = store.search(["integration"])
        found_after_delete = any(m["key"] == test_key for m in search_after_delete)
        assert not found_after_delete, "Deleted record should not be found"

    def test_firestore_error_handling(self, firestore_client):
        """Test Firestore error handling and fallback behavior."""
        collection_name = "test_error_handling"
        store = FirestoreStore(collection_name)

        # Test search with empty tags
        empty_results = store.search([])
        assert empty_results == [], "Search with empty tags should return empty list"

        # Test search with non-existent tags
        no_results = store.search(["nonexistent_tag_12345"])
        assert no_results == [], "Search for non-existent tags should return empty list"

        # Test that timestamps are properly formatted
        test_key = f"timestamp_test_{int(time.time())}"
        store.store(test_key, "timestamp test", ["timestamp"])

        results = store.search(["timestamp"])
        assert len(results) >= 1

        for result in results:
            if result["key"] == test_key:
                timestamp_str = result["timestamp"]
                # Verify timestamp is valid ISO format
                parsed_timestamp = datetime.fromisoformat(timestamp_str)
                assert isinstance(parsed_timestamp, datetime)
                break
        else:
            pytest.fail("Test record with timestamp not found")

    def test_firestore_connection_validation(self):
        """Test that FirestoreStore properly validates connection."""
        # Skip if environment not configured
        if not os.getenv("FRESH_USE_FIRESTORE", "").lower() == "true":
            pytest.skip("FRESH_USE_FIRESTORE not set to 'true'")

        if not os.getenv("FIRESTORE_EMULATOR_HOST"):
            pytest.skip("FIRESTORE_EMULATOR_HOST not configured")

        if not FIRESTORE_AVAILABLE:
            pytest.skip("google-cloud-firestore not available")

        # Create store and verify it connected successfully
        store = FirestoreStore("connection_test")

        # Should not use fallback when properly configured
        assert store._fallback_store is None, (
            "Should not use fallback with proper configuration"
        )
        assert store._client is not None, "Should have Firestore client"
        assert store._collection is not None, "Should have collection reference"


@pytest.mark.integration
class TestOpenAIIntegration:
    """Integration tests for OpenAI API."""

    @pytest.fixture
    def openai_client(self):
        """Create OpenAI client for testing."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not configured")

        if not OPENAI_AVAILABLE:
            pytest.skip("openai package not available")

        client = openai.OpenAI(api_key=api_key)
        return client

    @ci_skip
    def test_openai_embedding_integration(self, openai_client):
        """Test minimal cost OpenAI API integration with embeddings."""
        # Use a very short text to minimize cost
        test_text = "test"  # 1 token

        try:
            # Use the smallest, cheapest embedding model
            response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=test_text,
                dimensions=512,  # Use smaller dimensions to reduce cost
            )

            # Verify response structure
            assert hasattr(response, "data"), "Response should have data attribute"
            assert len(response.data) == 1, "Should have one embedding"

            embedding = response.data[0].embedding
            assert isinstance(embedding, list), "Embedding should be a list"
            assert len(embedding) == 512, "Embedding should have 512 dimensions"

            # Verify embedding values are reasonable
            assert all(isinstance(val, (int, float)) for val in embedding), (
                "All values should be numeric"
            )

            # Check that we got actual embeddings (not all zeros)
            non_zero_values = sum(1 for val in embedding if abs(val) > 1e-6)
            assert non_zero_values > 100, "Embedding should have many non-zero values"

        except openai.AuthenticationError:
            pytest.fail("OpenAI API authentication failed - check OPENAI_API_KEY")
        except openai.RateLimitError:
            pytest.skip("OpenAI API rate limit exceeded")
        except openai.APIError as e:
            pytest.fail(f"OpenAI API error: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error during OpenAI API call: {e}")

    @ci_skip
    def test_openai_api_key_validation(self):
        """Test that OpenAI API key is properly configured."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not configured")

        if not OPENAI_AVAILABLE:
            pytest.skip("openai package not available")

        # Basic validation of API key format
        assert isinstance(api_key, str), "API key should be a string"
        assert len(api_key) > 10, "API key should be reasonably long"
        assert api_key.startswith(("sk-", "sk-proj-")), (
            "API key should start with expected prefix"
        )

        # Test that client can be created
        client = openai.OpenAI(api_key=api_key)
        assert client is not None, "OpenAI client should be created successfully"

    @ci_skip
    def test_openai_minimal_completion(self, openai_client):
        """Test minimal completion to verify API connectivity."""
        try:
            # Use the cheapest model with minimal input
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,  # Minimize tokens to reduce cost
                temperature=0,  # Make response deterministic
            )

            # Verify response structure
            assert hasattr(response, "choices"), "Response should have choices"
            assert len(response.choices) > 0, "Should have at least one choice"

            choice = response.choices[0]
            assert hasattr(choice, "message"), "Choice should have message"
            assert hasattr(choice.message, "content"), "Message should have content"

            content = choice.message.content
            assert isinstance(content, str), "Content should be a string"
            assert len(content.strip()) > 0, "Content should not be empty"

        except openai.AuthenticationError:
            pytest.fail("OpenAI API authentication failed - check OPENAI_API_KEY")
        except openai.RateLimitError:
            pytest.skip("OpenAI API rate limit exceeded")
        except openai.APIError as e:
            pytest.fail(f"OpenAI API error: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error during OpenAI API call: {e}")


if __name__ == "__main__":
    # Run only integration tests
    pytest.main([__file__, "-v", "-m", "integration"])
