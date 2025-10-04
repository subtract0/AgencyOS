"""
Tests for Generic Persistent Store (shared/persistent_store.py)

NECESSARY Pattern Compliance:
- Named: Clear test names describing behavior
- Executable: Run independently and in suite
- Comprehensive: Cover success paths, edge cases, errors
- Error-validated: Test error conditions explicitly
- State-verified: Assert post-conditions
- Side-effects controlled: Clean temp files
- Assertions meaningful: Specific checks
- Repeatable: Deterministic results
- Yield fast: <1s per test

Constitutional Compliance:
- Article I: Complete context before action
- Article II: 100% verification and stability
- TDD: Tests written BEFORE implementation
"""

import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

import pytest

from shared.persistent_store import (
    PersistentStore,
    StoreEntry,
    StoreError,
    ValidationError,
)


class TestStoreInitialization:
    """Test store initialization and setup."""

    def test_creates_database_file_on_init(self):
        """Store creates SQLite database file when initialized with file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            store = PersistentStore(db_path=str(db_path))

            assert db_path.exists()
            assert db_path.stat().st_size > 0

            store.close()

    def test_supports_in_memory_database(self):
        """Store supports in-memory database for testing."""
        store = PersistentStore(db_path=":memory:")

        # Should work without file creation
        result = store.set("test_key", {"value": "test"})
        assert result.is_ok()

        store.close()

    def test_creates_custom_table_name(self):
        """Store creates table with custom name when specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            store = PersistentStore(db_path=str(db_path), table_name="custom_store")

            # Verify table exists
            cursor = store.conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='custom_store'
            """)
            result = cursor.fetchone()

            assert result is not None
            assert result[0] == "custom_store"

            store.close()

    def test_defaults_to_store_table_name(self):
        """Store defaults to 'store' table name if not specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            store = PersistentStore(db_path=str(db_path))

            cursor = store.conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='store'
            """)
            result = cursor.fetchone()

            assert result is not None

            store.close()

    def test_supports_context_manager(self):
        """Store supports context manager protocol."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            with PersistentStore(db_path=str(db_path)) as store:
                assert store.conn is not None
                result = store.set("test", {"data": "value"})
                assert result.is_ok()

            # Connection should be closed after context


class TestCRUDOperations:
    """Test Create, Read, Update, Delete operations."""

    def test_stores_new_entry_successfully(self):
        """Store persists new key-value entry."""
        store = PersistentStore(db_path=":memory:")

        result = store.set("user:123", {"name": "Alice", "role": "admin"})

        assert result.is_ok()

        store.close()

    def test_retrieves_stored_entry(self):
        """Store retrieves previously stored entry by key."""
        store = PersistentStore(db_path=":memory:")

        store.set("config:app", {"theme": "dark", "lang": "en"})
        result = store.get("config:app")

        assert result.is_ok()
        assert result.unwrap() is not None
        data = result.unwrap()
        assert data["theme"] == "dark"
        assert data["lang"] == "en"

        store.close()

    def test_updates_existing_entry(self):
        """Store updates value for existing key."""
        store = PersistentStore(db_path=":memory:")

        store.set("counter", {"value": 1})
        store.set("counter", {"value": 2})  # Update

        result = store.get("counter")
        assert result.is_ok()
        assert result.unwrap()["value"] == 2

        store.close()

    def test_deletes_entry_by_key(self):
        """Store removes entry when delete called."""
        store = PersistentStore(db_path=":memory:")

        store.set("temp", {"data": "temporary"})
        result = store.delete("temp")

        assert result.is_ok()

        # Verify deletion
        get_result = store.get("temp")
        assert get_result.is_ok()
        assert get_result.unwrap() is None

        store.close()

    def test_returns_none_for_nonexistent_key(self):
        """Store returns None when getting non-existent key."""
        store = PersistentStore(db_path=":memory:")

        result = store.get("nonexistent")

        assert result.is_ok()
        assert result.unwrap() is None

        store.close()

    def test_stores_complex_nested_data(self):
        """Store handles complex nested dictionaries."""
        store = PersistentStore(db_path=":memory:")

        complex_data = {
            "users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
            "metadata": {"version": "1.0", "tags": ["prod", "critical"]},
        }

        store.set("app:state", complex_data)
        result = store.get("app:state")

        assert result.is_ok()
        retrieved = result.unwrap()
        assert retrieved["users"][0]["name"] == "Alice"
        assert "critical" in retrieved["metadata"]["tags"]

        store.close()

    def test_stores_metadata_with_entry(self):
        """Store persists optional metadata alongside value."""
        store = PersistentStore(db_path=":memory:")

        metadata = {"source": "api", "version": "2.0"}
        result = store.set("data:123", {"content": "test"}, metadata=metadata)

        assert result.is_ok()

        # Retrieve and verify metadata
        entries = store.list_all()
        assert entries.is_ok()
        entry = next((e for e in entries.unwrap() if e.key == "data:123"), None)
        assert entry is not None
        assert entry.metadata["source"] == "api"

        store.close()


class TestQueryOperations:
    """Test query and listing operations."""

    def test_lists_all_keys(self):
        """Store lists all stored keys."""
        store = PersistentStore(db_path=":memory:")

        store.set("key1", {"a": 1})
        store.set("key2", {"b": 2})
        store.set("key3", {"c": 3})

        result = store.list_keys()

        assert result.is_ok()
        keys = result.unwrap()
        assert len(keys) == 3
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" in keys

        store.close()

    def test_lists_keys_with_prefix(self):
        """Store filters keys by prefix."""
        store = PersistentStore(db_path=":memory:")

        store.set("user:123", {"name": "Alice"})
        store.set("user:456", {"name": "Bob"})
        store.set("config:app", {"theme": "dark"})

        result = store.list_keys(prefix="user:")

        assert result.is_ok()
        keys = result.unwrap()
        assert len(keys) == 2
        assert "user:123" in keys
        assert "user:456" in keys
        assert "config:app" not in keys

        store.close()

    def test_lists_all_entries_with_values(self):
        """Store retrieves all entries with full data."""
        store = PersistentStore(db_path=":memory:")

        store.set("k1", {"val": 1})
        store.set("k2", {"val": 2})

        result = store.list_all()

        assert result.is_ok()
        entries = result.unwrap()
        assert len(entries) == 2
        assert all(isinstance(e, StoreEntry) for e in entries)
        assert all(e.value is not None for e in entries)

        store.close()

    def test_queries_with_filter_function(self):
        """Store filters entries using custom filter function."""
        store = PersistentStore(db_path=":memory:")

        store.set("user:1", {"age": 25, "active": True})
        store.set("user:2", {"age": 30, "active": False})
        store.set("user:3", {"age": 35, "active": True})

        # Filter for active users over 25
        def filter_active_adults(entry: StoreEntry) -> bool:
            return entry.value.get("active", False) and entry.value.get("age", 0) > 25

        result = store.query(filter_active_adults)

        assert result.is_ok()
        entries = result.unwrap()
        assert len(entries) == 1  # Only user:3 matches
        assert entries[0].value["age"] == 35

        store.close()

    def test_query_returns_empty_list_when_no_matches(self):
        """Store returns empty list when no entries match filter."""
        store = PersistentStore(db_path=":memory:")

        store.set("k1", {"val": 1})

        result = store.query(lambda e: e.value.get("val") > 100)

        assert result.is_ok()
        assert len(result.unwrap()) == 0

        store.close()


class TestTimestamps:
    """Test timestamp tracking for entries."""

    def test_sets_created_at_on_insert(self):
        """Store sets created_at timestamp when entry created."""
        store = PersistentStore(db_path=":memory:")

        before = datetime.now()
        store.set("test", {"data": "value"})
        after = datetime.now()

        entries = store.list_all()
        entry = entries.unwrap()[0]

        assert before <= entry.created_at <= after

        store.close()

    def test_updates_updated_at_on_modification(self):
        """Store updates updated_at timestamp when entry modified."""
        store = PersistentStore(db_path=":memory:")

        store.set("test", {"data": "v1"})
        time.sleep(0.01)  # Small delay to ensure different timestamps

        store.set("test", {"data": "v2"})

        entries = store.list_all()
        entry = entries.unwrap()[0]

        # updated_at should be later than created_at
        assert entry.updated_at > entry.created_at

        store.close()

    def test_created_at_unchanged_on_update(self):
        """Store preserves created_at timestamp when entry updated."""
        store = PersistentStore(db_path=":memory:")

        store.set("test", {"data": "v1"})
        entries = store.list_all()
        original_created = entries.unwrap()[0].created_at

        time.sleep(0.01)
        store.set("test", {"data": "v2"})

        entries = store.list_all()
        updated_created = entries.unwrap()[0].created_at

        assert original_created == updated_created

        store.close()


class TestConcurrency:
    """Test thread-safety and concurrent access."""

    def test_handles_concurrent_writes(self):
        """Store safely handles concurrent writes from multiple threads."""
        store = PersistentStore(db_path=":memory:")

        def write_entries(thread_id: int):
            for i in range(10):
                store.set(f"thread{thread_id}:item{i}", {"tid": thread_id, "val": i})

        threads = [threading.Thread(target=write_entries, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify all entries written
        result = store.list_keys()
        assert result.is_ok()
        keys = result.unwrap()
        assert len(keys) == 50  # 5 threads * 10 items each

        store.close()

    def test_handles_concurrent_read_write(self):
        """Store handles simultaneous reads and writes."""
        store = PersistentStore(db_path=":memory:")

        # Pre-populate
        for i in range(10):
            store.set(f"key{i}", {"val": i})

        def read_entries():
            for i in range(20):
                store.get(f"key{i % 10}")

        def write_entries():
            for i in range(10, 20):
                store.set(f"key{i}", {"val": i})

        read_thread = threading.Thread(target=read_entries)
        write_thread = threading.Thread(target=write_entries)

        read_thread.start()
        write_thread.start()

        read_thread.join()
        write_thread.join()

        # No exceptions = success
        store.close()


class TestPersistence:
    """Test data persistence across store instances."""

    def test_persists_data_across_close_and_reopen(self):
        """Store persists data when closed and reopened."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "persist.db"

            # Write data
            store1 = PersistentStore(db_path=str(db_path))
            store1.set("persistent", {"data": "saved"})
            store1.close()

            # Read data with new instance
            store2 = PersistentStore(db_path=str(db_path))
            result = store2.get("persistent")

            assert result.is_ok()
            assert result.unwrap()["data"] == "saved"

            store2.close()

    def test_maintains_timestamps_across_reload(self):
        """Store preserves timestamps when reloading database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "timestamps.db"

            store1 = PersistentStore(db_path=str(db_path))
            store1.set("test", {"val": 1})
            entries1 = store1.list_all()
            original_created = entries1.unwrap()[0].created_at
            store1.close()

            store2 = PersistentStore(db_path=str(db_path))
            entries2 = store2.list_all()
            reloaded_created = entries2.unwrap()[0].created_at

            assert original_created == reloaded_created

            store2.close()


class TestErrorHandling:
    """Test error conditions and validation."""

    def test_returns_error_for_invalid_value_type(self):
        """Store returns error when value is not a dict."""
        store = PersistentStore(db_path=":memory:")

        # Value must be a dict
        result = store.set("key", "not a dict")  # type: ignore

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, ValidationError)
        assert "dict" in str(error).lower()

        store.close()

    def test_returns_error_for_empty_key(self):
        """Store returns error when key is empty string."""
        store = PersistentStore(db_path=":memory:")

        result = store.set("", {"data": "value"})

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, ValidationError)
        assert "key" in str(error).lower()

        store.close()

    def test_returns_error_when_closed(self):
        """Store returns error when operations attempted after close."""
        store = PersistentStore(db_path=":memory:")
        store.close()

        result = store.set("test", {"data": "value"})

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, StoreError)

        # Don't call close again

    def test_handles_database_errors_gracefully(self):
        """Store handles database corruption or errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            store = PersistentStore(db_path=str(db_path))

            # Corrupt the connection
            store.conn.close()
            store.conn = None  # Simulate corruption

            result = store.get("test")

            assert result.is_err()
            assert isinstance(result.unwrap_err(), StoreError)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_handles_unicode_keys(self):
        """Store handles Unicode characters in keys."""
        store = PersistentStore(db_path=":memory:")

        result = store.set("用户:123", {"name": "测试"})
        assert result.is_ok()

        get_result = store.get("用户:123")
        assert get_result.is_ok()
        assert get_result.unwrap()["name"] == "测试"

        store.close()

    def test_handles_very_long_keys(self):
        """Store handles long key strings."""
        store = PersistentStore(db_path=":memory:")

        long_key = "x" * 1000
        result = store.set(long_key, {"data": "test"})

        assert result.is_ok()

        get_result = store.get(long_key)
        assert get_result.is_ok()
        assert get_result.unwrap()["data"] == "test"

        store.close()

    def test_handles_large_value_payloads(self):
        """Store handles large data values."""
        store = PersistentStore(db_path=":memory:")

        large_data = {"items": [{"id": i, "data": "x" * 100} for i in range(1000)]}

        result = store.set("large", large_data)
        assert result.is_ok()

        get_result = store.get("large")
        assert get_result.is_ok()
        assert len(get_result.unwrap()["items"]) == 1000

        store.close()

    def test_handles_empty_metadata(self):
        """Store handles empty metadata dict."""
        store = PersistentStore(db_path=":memory:")

        result = store.set("test", {"data": "value"}, metadata={})

        assert result.is_ok()

        store.close()

    def test_returns_empty_list_for_empty_database(self):
        """Store returns empty list when database has no entries."""
        store = PersistentStore(db_path=":memory:")

        result = store.list_keys()
        assert result.is_ok()
        assert len(result.unwrap()) == 0

        result = store.list_all()
        assert result.is_ok()
        assert len(result.unwrap()) == 0

        store.close()


class TestStoreEntryModel:
    """Test StoreEntry Pydantic model."""

    def test_creates_valid_entry_from_data(self):
        """StoreEntry validates and creates from valid data."""
        entry = StoreEntry(
            key="test",
            value={"data": "value"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={"source": "test"},
        )

        assert entry.key == "test"
        assert entry.value["data"] == "value"
        assert entry.metadata["source"] == "test"

    def test_defaults_empty_metadata(self):
        """StoreEntry defaults to empty dict for metadata."""
        entry = StoreEntry(
            key="test", value={}, created_at=datetime.now(), updated_at=datetime.now()
        )

        assert entry.metadata == {}

    def test_validates_value_is_dict(self):
        """StoreEntry validates that value is a dict."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            StoreEntry(
                key="test",
                value="not a dict",  # type: ignore
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
