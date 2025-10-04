"""
Type conversion utilities for memory operations.

Provides centralized type conversions and caching to optimize performance
by reducing repeated isinstance() calls.
"""

from datetime import datetime
from typing import Any, cast

from shared.models.memory import MemoryMetadata, MemoryPriority, MemoryRecord
from shared.type_definitions.json import JSONValue


class TypeConversionCache:
    """Cache for type check results to minimize repeated isinstance() calls."""

    def __init__(self):
        self._type_cache: dict[int, dict[str, bool]] = {}

    def is_list(self, value: Any) -> bool:
        """Check if value is a list with caching."""
        obj_id = id(value)
        if obj_id not in self._type_cache:
            self._type_cache[obj_id] = {}

        if "is_list" not in self._type_cache[obj_id]:
            self._type_cache[obj_id]["is_list"] = isinstance(value, list)

        return self._type_cache[obj_id]["is_list"]

    def is_string(self, value: Any) -> bool:
        """Check if value is a string with caching."""
        obj_id = id(value)
        if obj_id not in self._type_cache:
            self._type_cache[obj_id] = {}

        if "is_string" not in self._type_cache[obj_id]:
            self._type_cache[obj_id]["is_string"] = isinstance(value, str)

        return self._type_cache[obj_id]["is_string"]

    def is_number(self, value: Any) -> bool:
        """Check if value is a number (int or float) with caching."""
        obj_id = id(value)
        if obj_id not in self._type_cache:
            self._type_cache[obj_id] = {}

        if "is_number" not in self._type_cache[obj_id]:
            self._type_cache[obj_id]["is_number"] = isinstance(value, (int, float))

        return self._type_cache[obj_id]["is_number"]

    def clear(self) -> None:
        """Clear the type cache."""
        self._type_cache.clear()


class MemoryConverter:
    """Utility class for converting memory data between different formats."""

    def __init__(self, type_cache: TypeConversionCache | None = None):
        self.type_cache = type_cache or TypeConversionCache()

    def extract_tags_list(self, tags_value: Any) -> list[str]:
        """
        Extract tags as string list with type safety.

        Args:
            tags_value: Raw tags value from memory

        Returns:
            List of string tags, empty if invalid
        """
        if not self.type_cache.is_list(tags_value):
            return []

        return [str(tag) for tag in tags_value if self.type_cache.is_string(tag)]

    def safe_string_conversion(self, value: Any, default: str = "") -> str:
        """
        Safely convert value to string.

        Args:
            value: Value to convert
            default: Default value if conversion fails

        Returns:
            String representation or default
        """
        if self.type_cache.is_string(value):
            return value
        return str(value) if value is not None else default

    def safe_timestamp_conversion(self, timestamp_value: Any) -> datetime:
        """
        Safely convert timestamp value to datetime.

        Args:
            timestamp_value: Raw timestamp value

        Returns:
            datetime object, current time if conversion fails
        """
        try:
            if self.type_cache.is_string(timestamp_value):
                return datetime.fromisoformat(timestamp_value)
            return datetime.now()
        except (ValueError, TypeError):
            return datetime.now()

    def memory_dict_to_record(self, memory_dict: dict[str, JSONValue]) -> MemoryRecord | None:
        """
        Convert memory dictionary to MemoryRecord with type safety.

        Args:
            memory_dict: Raw memory dictionary

        Returns:
            MemoryRecord or None if conversion fails
        """
        try:
            # Extract tags with type validation
            tags_value = memory_dict.get("tags", [])
            tags_list = self.extract_tags_list(tags_value)

            # Extract other fields with type safety
            key = self.safe_string_conversion(memory_dict.get("key", ""))
            content = memory_dict.get("content", "")
            timestamp = self.safe_timestamp_conversion(memory_dict.get("timestamp"))

            return MemoryRecord(
                key=key,
                content=content,
                tags=tags_list,
                timestamp=timestamp,
                priority=MemoryPriority.LOW,
                metadata=MemoryMetadata(),
                ttl_seconds=None,
                embedding=None,
            )
        except Exception:
            return None

    def record_to_dict(self, record: MemoryRecord) -> dict[str, JSONValue]:
        """
        Convert MemoryRecord to dictionary format.

        Args:
            record: MemoryRecord to convert

        Returns:
            Dictionary representation
        """
        return {
            "key": record.key,
            "content": record.content,
            "tags": cast(JSONValue, record.tags),
            "timestamp": record.timestamp.isoformat(),
            "priority": record.priority.value,
        }

    def add_relevance_score(
        self, memory_dict: dict[str, JSONValue], score: float, search_type: str
    ) -> dict[str, JSONValue]:
        """
        Add relevance score and search type to memory dictionary.

        Args:
            memory_dict: Base memory dictionary
            score: Relevance score
            search_type: Type of search that produced this result

        Returns:
            Enhanced dictionary with score and search type
        """
        enhanced_dict = memory_dict.copy()
        enhanced_dict["relevance_score"] = score
        enhanced_dict["search_type"] = search_type
        return enhanced_dict


def create_memory_converter() -> MemoryConverter:
    """
    Factory function to create a MemoryConverter with a fresh type cache.

    Returns:
        New MemoryConverter instance
    """
    return MemoryConverter()
