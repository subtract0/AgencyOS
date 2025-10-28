"""
Pytest fixtures for agency_memory tests.

Ensures proper test isolation by cleaning VectorStore state between tests.
"""

import pytest
from pathlib import Path
import shutil
import os


@pytest.fixture(autouse=True)
def clean_vectorstore_state(request, tmp_path, monkeypatch):
    """
    Auto-use fixture to clean VectorStore state before each test.

    Ensures test isolation by:
    - Using unique temp storage for each test
    - Clearing any in-memory VectorStore instances
    - Preventing shared state between tests

    Integration tests (ending with _integration.py) get real persistence behavior.
    Unit tests get isolated, ephemeral storage.

    Article II Requirement: Tests must be isolated and repeatable.
    """
    # Check if this is an integration test (needs real persistence)
    test_file = request.node.fspath.basename
    is_integration_test = "integration" in test_file

    # Create unique test storage directory
    test_storage = tmp_path / "vectorstore_test"
    test_storage.mkdir(parents=True, exist_ok=True)

    if not is_integration_test:
        # Unit tests: Mock VectorStore for isolation (no disk I/O)
        def mock_init(self, embedding_provider=None, storage_path=None):
            """Patched __init__ that uses ephemeral storage."""
            self._embeddings = {}
            self._memory_texts = {}
            self._memory_records = {}
            self._embedding_provider = embedding_provider
            self._embedding_function = None
            self.storage_path = storage_path or str(test_storage)
            # Skip embedding initialization (too slow)
            # Skip loading from disk (test isolation)

        from agency_memory import vector_store
        monkeypatch.setattr(vector_store.VectorStore, "__init__", mock_init)
    else:
        # Integration tests: Use real VectorStore with test storage
        # Patch the default storage path to use test directory
        def get_test_storage_path():
            return str(test_storage)

        import agency_memory.vector_store as vs
        original_init = vs.VectorStore.__init__

        def patched_init(self, embedding_provider=None, storage_path=None):
            # Use test storage unless explicitly provided
            if storage_path is None:
                storage_path = str(test_storage)
            original_init(self, embedding_provider, storage_path)

        monkeypatch.setattr(vs.VectorStore, "__init__", patched_init)

    yield

    # Clean up after test
    if test_storage.exists():
        shutil.rmtree(test_storage)


@pytest.fixture
def temp_vectorstore_path(tmp_path):
    """
    Provide a temporary directory for VectorStore persistence tests.

    Returns:
        Path: Temporary directory path for VectorStore storage
    """
    storage_path = tmp_path / "vectorstore"
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path
