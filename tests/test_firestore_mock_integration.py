"""
Mock-based Firestore integration tests.

These tests exercise the Firestore integration code paths using mocks
when the actual Firestore emulator is not available (e.g., no Java installed).
"""

import os
import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from agency_memory import FirestoreStore


@pytest.mark.integration
class TestFirestoreMockIntegration:
    """Mock-based integration tests for Firestore functionality."""

    @pytest.fixture
    def mock_firestore_client(self):
        """Create a mock Firestore client that behaves like the real one."""
        with patch("agency_memory.firestore_store.firestore") as mock_firestore:
            # Create mock client
            mock_client = MagicMock()
            mock_firestore.Client.return_value = mock_client

            # Storage for mock documents
            mock_storage = {}

            # Mock collection
            mock_collection = MagicMock()
            mock_client.collection.return_value = mock_collection

            # Mock document operations
            def mock_document(doc_id):
                mock_doc_ref = MagicMock()
                mock_doc_ref.id = doc_id

                def mock_set(data):
                    mock_storage[doc_id] = data

                def mock_get():
                    mock_doc = MagicMock()
                    if doc_id in mock_storage:
                        mock_doc.exists = True
                        mock_doc.to_dict.return_value = mock_storage[doc_id]
                    else:
                        mock_doc.exists = False
                    return mock_doc

                def mock_delete():
                    if doc_id in mock_storage:
                        del mock_storage[doc_id]

                mock_doc_ref.set = mock_set
                mock_doc_ref.get = mock_get
                mock_doc_ref.delete = mock_delete

                return mock_doc_ref

            mock_collection.document = mock_document

            # Mock where queries
            def mock_where(field, op, value):
                mock_query = MagicMock()

                def mock_stream():
                    results = []
                    for doc_id, doc_data in mock_storage.items():
                        if field == "tags":
                            doc_tags = doc_data.get("tags", [])
                            if op == "array_contains":
                                # Single value check
                                if value in doc_tags:
                                    mock_doc = MagicMock()
                                    mock_doc.id = doc_id
                                    mock_doc.to_dict.return_value = doc_data
                                    mock_doc.reference = mock_document(doc_id)
                                    results.append(mock_doc)
                            elif op == "array_contains_any":
                                # Multiple values check - any match
                                if any(tag in doc_tags for tag in value):
                                    mock_doc = MagicMock()
                                    mock_doc.id = doc_id
                                    mock_doc.to_dict.return_value = doc_data
                                    mock_doc.reference = mock_document(doc_id)
                                    results.append(mock_doc)
                    return results

                def mock_limit(count):
                    limited_query = MagicMock()

                    def mock_limited_stream():
                        all_results = mock_stream()
                        return all_results[:count]

                    limited_query.stream = mock_limited_stream
                    return limited_query

                mock_query.stream = mock_stream
                mock_query.limit = mock_limit
                return mock_query

            mock_collection.where = mock_where

            # Mock stream for all documents
            def mock_stream_all():
                results = []
                for doc_id, doc_data in mock_storage.items():
                    mock_doc = MagicMock()
                    mock_doc.id = doc_id
                    mock_doc.to_dict.return_value = doc_data
                    mock_doc.reference = mock_document(doc_id)
                    results.append(mock_doc)
                return results

            # Mock limit for connection testing
            def mock_limit(count):
                limited_query = MagicMock()

                def mock_limited_stream():
                    all_results = mock_stream_all()
                    return all_results[:count]

                limited_query.stream = mock_limited_stream
                return limited_query

            mock_collection.stream = mock_stream_all
            mock_collection.limit = mock_limit

            # Set environment variables
            with patch.dict(
                os.environ,
                {
                    "FRESH_USE_FIRESTORE": "true",
                    "FIRESTORE_EMULATOR_HOST": "localhost:8080",
                    "GOOGLE_CLOUD_PROJECT": "agency-test",
                },
            ):
                yield mock_client, mock_storage

    def test_firestore_crud_operations(self, mock_firestore_client):
        """Test complete CRUD operations with mocked Firestore."""
        mock_client, mock_storage = mock_firestore_client

        collection_name = "test_integration_memories"
        test_key = f"integration_test_{int(time.time())}"
        test_content = "Integration test content"
        test_tags = ["integration", "test", "firestore"]

        # Create a FirestoreStore instance
        store = FirestoreStore(collection_name)

        # Verify Firestore is being used (not fallback)
        assert store._client is not None
        assert store._fallback_store is None

        # Verify the collection is connected to our mock
        assert store._collection is not None

        # Test CREATE operation
        store.store(test_key, test_content, test_tags)

        # Verify data was stored
        assert test_key in mock_storage
        stored_data = mock_storage[test_key]
        assert stored_data["key"] == test_key
        assert stored_data["content"] == test_content
        assert stored_data["tags"] == test_tags
        assert "timestamp" in stored_data

        # Test READ operation via search
        search_results = store.search(["integration"])
        assert search_results.total_count >= 1

        found_record = False
        for result in search_results.records:
            if result.key == test_key:
                found_record = True
                assert result.content == test_content
                assert set(test_tags).issubset(set(result.tags))
                break

        assert found_record, "Created record should be found in search results"

        # Test UPDATE operation
        updated_content = "Updated integration test content"
        updated_tags = ["integration", "test", "updated", "firestore"]
        store.store(test_key, updated_content, updated_tags)

        # Verify update
        search_after_update = store.search(["updated"])
        found_updated = False
        for result in search_after_update.records:
            if result.key == test_key:
                found_updated = True
                assert result.content == updated_content
                assert "updated" in result.tags
                break

        assert found_updated, "Updated record should be found with new tag"

        # Test DELETE operation
        store._collection.document(test_key).delete()

        # Verify deletion
        assert test_key not in mock_storage

    def test_firestore_error_handling(self, mock_firestore_client):
        """Test Firestore error handling with mocks."""
        mock_client, mock_storage = mock_firestore_client

        collection_name = "test_error_handling"
        store = FirestoreStore(collection_name)

        # Test search with empty tags
        empty_results = store.search([])
        assert empty_results.total_count == 0

        # Test search with non-existent tags
        no_results = store.search(["nonexistent_tag_12345"])
        assert no_results.total_count == 0

        # Test timestamp formatting
        test_key = f"timestamp_test_{int(time.time())}"
        store.store(test_key, "timestamp test", ["timestamp"])

        results = store.search(["timestamp"])
        assert results.total_count >= 1

        for result in results.records:
            if result.key == test_key:
                timestamp_str = result.timestamp.isoformat()
                # Verify timestamp is valid ISO format
                parsed_timestamp = datetime.fromisoformat(timestamp_str)
                assert isinstance(parsed_timestamp, datetime)
                break
        else:
            pytest.fail("Test record with timestamp not found")

    def test_firestore_connection_validation(self, mock_firestore_client):
        """Test FirestoreStore connection validation with mocks."""
        mock_client, mock_storage = mock_firestore_client

        # Create store and verify it connected successfully
        store = FirestoreStore("connection_test")

        # Should not use fallback when properly configured
        assert store._fallback_store is None
        assert store._client is not None
        assert store._collection is not None

    def test_firestore_batch_operations(self, mock_firestore_client):
        """Test batch operations with mocked Firestore."""
        mock_client, mock_storage = mock_firestore_client

        store = FirestoreStore("batch_test")

        # Store multiple items
        batch_size = 10
        for i in range(batch_size):
            key = f"batch_item_{i}"
            content = f"Batch content {i}"
            tags = ["batch", f"item_{i}"]
            store.store(key, content, tags)

        # Search for all batch items
        batch_results = store.search(["batch"])
        assert batch_results.total_count == batch_size

        # Verify all items are present
        found_keys = {r.key for r in batch_results.records}
        expected_keys = {f"batch_item_{i}" for i in range(batch_size)}
        assert found_keys == expected_keys
