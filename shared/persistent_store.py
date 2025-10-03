"""
Generic Persistent Store for Agency

Provides a thread-safe, SQLite-backed key-value store with metadata support.
Designed to be reusable across agents without domain-specific coupling.

Constitutional Compliance:
- Article I: Complete context - data persists across sessions
- Article II: 100% verification - Result pattern for errors
- TDD: Implementation follows comprehensive test suite

Architecture:
- Generic key-value storage (no domain-specific schemas)
- Pluggable table names for multi-tenant scenarios
- Thread-safe operations with lock protection
- Result<T,E> pattern for error handling
- Pydantic models for type safety
"""

import sqlite3
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
from pydantic import BaseModel, field_validator

from shared.type_definitions.result import Result, Ok, Err


class StoreError(Exception):
    """Base exception for persistent store errors."""
    pass


class NotFoundError(StoreError):
    """Exception raised when key not found."""
    pass


class ValidationError(StoreError):
    """Exception raised for validation failures."""
    pass


class StoreEntry(BaseModel):
    """
    Single entry in the persistent store.

    Attributes:
        key: Unique identifier for the entry
        value: Dict containing the stored data
        created_at: Timestamp when entry was created
        updated_at: Timestamp when entry was last modified
        metadata: Optional metadata dict for tagging/filtering
    """
    key: str
    value: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, str] = {}

    @field_validator('value')
    @classmethod
    def validate_value_is_dict(cls, v: Any) -> Dict[str, Any]:
        """Ensure value is a dictionary."""
        if not isinstance(v, dict):
            raise ValueError("Value must be a dict")
        return v


class PersistentStore:
    """
    Generic persistent key-value store backed by SQLite.

    Provides thread-safe CRUD operations with optional metadata tagging.
    Designed for reuse across multiple agents and use cases.

    Example:
        >>> store = PersistentStore(db_path="app.db", table_name="config")
        >>> store.set("theme", {"color": "dark", "font": "mono"})
        >>> result = store.get("theme")
        >>> if result.is_ok():
        ...     print(result.unwrap()["color"])  # "dark"
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        table_name: str = "store"
    ):
        """
        Initialize persistent store.

        Args:
            db_path: Path to SQLite database (or ":memory:" for in-memory)
            table_name: Name of the storage table
        """
        self.db_path = Path(db_path) if db_path != ":memory:" else db_path
        self.table_name = table_name
        self.conn: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()

        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database with generic schema."""
        with self._lock:
            self.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self.conn.row_factory = sqlite3.Row

            cursor = self.conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT
                )
            """)

            # Index for prefix queries
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_key
                ON {self.table_name}(key)
            """)

            self.conn.commit()

    def _validate_set_inputs(
        self,
        key: str,
        value: Dict[str, Any]
    ) -> Optional[StoreError]:
        """Validate inputs for set operation. Returns error if invalid."""
        if not key or not isinstance(key, str):
            return ValidationError("Key must be a non-empty string")
        if not isinstance(value, dict):
            return ValidationError("Value must be a dict")
        if not self.conn:
            return StoreError("Database not initialized")
        return None

    def _upsert_entry(
        self,
        cursor: sqlite3.Cursor,
        key: str,
        value_json: str,
        metadata_json: Optional[str],
        now: str
    ) -> None:
        """Insert or update entry in database."""
        cursor.execute(
            f"SELECT created_at FROM {self.table_name} WHERE key = ?",
            (key,)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(f"""
                UPDATE {self.table_name}
                SET value = ?, updated_at = ?, metadata = ?
                WHERE key = ?
            """, (value_json, now, metadata_json, key))
        else:
            cursor.execute(f"""
                INSERT INTO {self.table_name}
                (key, value, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (key, value_json, now, now, metadata_json))

    def set(
        self,
        key: str,
        value: Dict[str, Any],
        metadata: Optional[Dict[str, str]] = None
    ) -> Result[None, StoreError]:
        """
        Store or update a key-value entry.

        Args:
            key: Unique identifier for the entry
            value: Data to store (must be a dict)
            metadata: Optional metadata for tagging/filtering

        Returns:
            Result[None, StoreError]: Ok(None) on success, Err on failure
        """
        validation_error = self._validate_set_inputs(key, value)
        if validation_error:
            return Err(validation_error)

        try:
            with self._lock:
                now = datetime.now().isoformat()
                value_json = json.dumps(value)
                metadata_json = json.dumps(metadata) if metadata else None

                cursor = self.conn.cursor()
                self._upsert_entry(cursor, key, value_json, metadata_json, now)
                self.conn.commit()
                return Ok(None)

        except Exception as e:
            return Err(StoreError(f"Failed to store entry: {e}"))

    def get(self, key: str) -> Result[Optional[Dict[str, Any]], StoreError]:
        """
        Retrieve value for a key.

        Args:
            key: Key to retrieve

        Returns:
            Result[Optional[Dict], StoreError]: Ok(value) if found,
                Ok(None) if not found, Err on failure
        """
        if not self.conn:
            return Err(StoreError("Database not initialized"))

        try:
            with self._lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    f"SELECT value FROM {self.table_name} WHERE key = ?",
                    (key,)
                )
                row = cursor.fetchone()

                if row is None:
                    return Ok(None)

                value = json.loads(row['value'])
                return Ok(value)

        except Exception as e:
            return Err(StoreError(f"Failed to retrieve entry: {e}"))

    def delete(self, key: str) -> Result[None, StoreError]:
        """
        Delete an entry by key.

        Args:
            key: Key to delete

        Returns:
            Result[None, StoreError]: Ok(None) on success, Err on failure
        """
        if not self.conn:
            return Err(StoreError("Database not initialized"))

        try:
            with self._lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    f"DELETE FROM {self.table_name} WHERE key = ?",
                    (key,)
                )
                self.conn.commit()
                return Ok(None)

        except Exception as e:
            return Err(StoreError(f"Failed to delete entry: {e}"))

    def list_keys(self, prefix: str = "") -> Result[List[str], StoreError]:
        """
        List all keys, optionally filtered by prefix.

        Args:
            prefix: Optional key prefix for filtering

        Returns:
            Result[List[str], StoreError]: Ok(keys) on success, Err on failure
        """
        if not self.conn:
            return Err(StoreError("Database not initialized"))

        try:
            with self._lock:
                cursor = self.conn.cursor()

                if prefix:
                    cursor.execute(
                        f"SELECT key FROM {self.table_name} WHERE key LIKE ?",
                        (f"{prefix}%",)
                    )
                else:
                    cursor.execute(f"SELECT key FROM {self.table_name}")

                rows = cursor.fetchall()
                keys = [row['key'] for row in rows]
                return Ok(keys)

        except Exception as e:
            return Err(StoreError(f"Failed to list keys: {e}"))

    def list_all(self) -> Result[List[StoreEntry], StoreError]:
        """
        Retrieve all entries with full data.

        Returns:
            Result[List[StoreEntry], StoreError]: Ok(entries) on success,
                Err on failure
        """
        if not self.conn:
            return Err(StoreError("Database not initialized"))

        try:
            with self._lock:
                cursor = self.conn.cursor()
                cursor.execute(f"SELECT * FROM {self.table_name}")
                rows = cursor.fetchall()

                entries = []
                for row in rows:
                    entry = StoreEntry(
                        key=row['key'],
                        value=json.loads(row['value']),
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at']),
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    )
                    entries.append(entry)

                return Ok(entries)

        except Exception as e:
            return Err(StoreError(f"Failed to list entries: {e}"))

    def query(
        self,
        filter_func: Callable[[StoreEntry], bool]
    ) -> Result[List[StoreEntry], StoreError]:
        """
        Query entries using a custom filter function.

        Args:
            filter_func: Function that takes StoreEntry and returns bool

        Returns:
            Result[List[StoreEntry], StoreError]: Ok(matching entries),
                Err on failure

        Example:
            >>> result = store.query(lambda e: e.value.get("active", False))
        """
        all_entries_result = self.list_all()

        if all_entries_result.is_err():
            return Err(all_entries_result.unwrap_err())

        try:
            all_entries = all_entries_result.unwrap()
            filtered = [e for e in all_entries if filter_func(e)]
            return Ok(filtered)

        except Exception as e:
            return Err(StoreError(f"Failed to query entries: {e}"))

    def store_pattern(
        self,
        pattern_type: str,
        pattern_name: str,
        content: str,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None,
        evidence_count: int = 1
    ) -> Result[str, StoreError]:
        """
        Store a pattern with a standardized structure.

        This is a convenience method that wraps set() with a pattern-specific
        key format and data structure.

        Args:
            pattern_type: Type of pattern (e.g., "action_item", "recurring_topic")
            pattern_name: Name/topic of the pattern
            content: Pattern content/description
            confidence: Confidence score (0.0-1.0)
            metadata: Optional additional metadata
            evidence_count: Number of evidence occurrences

        Returns:
            Result[str, StoreError]: Ok(pattern_id) on success, Err on failure
        """
        # Generate unique pattern ID
        timestamp = datetime.now().isoformat()
        pattern_id = f"{pattern_type}:{pattern_name}:{timestamp}"

        # Construct pattern data
        pattern_data = {
            "pattern_type": pattern_type,
            "pattern_name": pattern_name,
            "content": content,
            "confidence": confidence,
            "evidence_count": evidence_count,
            "timestamp": timestamp,
        }

        # Merge additional metadata if provided
        if metadata:
            pattern_data["metadata"] = metadata

        # Store using set() method
        result = self.set(
            key=pattern_id,
            value=pattern_data,
            metadata={
                "pattern_type": pattern_type,
                "pattern_name": pattern_name,
            }
        )

        if result.is_err():
            return Err(result.unwrap_err())

        return Ok(pattern_id)

    def search_patterns(
        self,
        pattern_type: Optional[str] = None,
        pattern_name: Optional[str] = None,
        query: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> Result[List[Dict[str, Any]], StoreError]:
        """
        Search for patterns by type, name, query text, and/or confidence.

        Args:
            pattern_type: Optional pattern type filter
            pattern_name: Optional pattern name filter
            query: Optional text query to search in pattern summary
            min_confidence: Optional minimum confidence threshold

        Returns:
            Result[List[Dict], StoreError]: Ok(patterns) on success, Err on failure
        """
        all_entries_result = self.list_all()

        if all_entries_result.is_err():
            return Err(all_entries_result.unwrap_err())

        try:
            all_entries = all_entries_result.unwrap()
            patterns = []

            for entry in all_entries:
                # Check if this is a pattern entry
                if "pattern_type" not in entry.value:
                    continue

                # Apply filters
                if pattern_type and entry.value.get("pattern_type") != pattern_type:
                    continue

                if pattern_name and entry.value.get("pattern_name") != pattern_name:
                    continue

                # Filter by query text (case-insensitive search in summary)
                if query:
                    summary = entry.value.get("summary", "").lower()
                    if query.lower() not in summary:
                        continue

                # Filter by minimum confidence
                if min_confidence is not None:
                    confidence = entry.value.get("confidence", 0.0)
                    if confidence < min_confidence:
                        continue

                patterns.append(entry.value)

            return Ok(patterns)

        except Exception as e:
            return Err(StoreError(f"Failed to search patterns: {e}"))

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the store.

        Returns:
            Dictionary with store statistics
        """
        if not self.conn:
            return {
                "total_patterns": 0,
                "total_entries": 0,
                "database_connected": False
            }

        try:
            with self._lock:
                cursor = self.conn.cursor()

                # Get total entry count
                cursor.execute(f"SELECT COUNT(*) as count FROM {self.table_name}")
                total_entries = cursor.fetchone()['count']

                # Get pattern count (entries with pattern_type metadata)
                cursor.execute(
                    f"SELECT COUNT(*) as count FROM {self.table_name} "
                    f"WHERE value LIKE '%pattern_type%'"
                )
                pattern_count = cursor.fetchone()['count']

                return {
                    "total_patterns": pattern_count,
                    "total_entries": total_entries,
                    "database_connected": True,
                    "table_name": self.table_name
                }

        except Exception as e:
            return {
                "total_patterns": 0,
                "total_entries": 0,
                "database_connected": False,
                "error": str(e)
            }

    def close(self) -> None:
        """Close database connection."""
        with self._lock:
            if self.conn:
                self.conn.close()
                self.conn = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
