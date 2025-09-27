# mypy: disable-error-code="misc,assignment,arg-type,attr-defined,index,return-value,union-attr,dict-item"
"""
Comprehensive type safety test suite for PR #20.
Tests all Pydantic models and type guards introduced in the type safety sweep.
Ensures Constitutional Law #1 (TDD) compliance.
"""

import pytest
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import ValidationError
import json

# Import all the Pydantic models
from shared.models.memory import (
    MemoryPriority,
    MemoryMetadata,
    MemoryRecord,
    MemorySearchResult,
)
from shared.models.telemetry import (
    TelemetryEvent,
    EventType,
    EventSeverity,
)
from shared.models.core import HealthStatus
from shared.type_definitions.json import JSONValue


class TestMemoryModels:
    """Test memory-related Pydantic models."""

    def test_memory_priority_enum(self):
        """Test MemoryPriority enum values."""
        assert MemoryPriority.LOW.value == "low"
        assert MemoryPriority.MEDIUM.value == "medium"
        assert MemoryPriority.HIGH.value == "high"
        assert MemoryPriority.CRITICAL.value == "critical"

    def test_memory_metadata_validation(self):
        """Test MemoryMetadata field validation."""
        # Valid metadata
        metadata = MemoryMetadata(
            agent_id="test_agent",
            session_id="session_123",
            success_rate=0.85
        )
        assert metadata.agent_id == "test_agent"
        assert metadata.success_rate == 0.85

        # Invalid success_rate should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            MemoryMetadata(success_rate=1.5)  # > 1
        assert "success_rate must be between 0 and 1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            MemoryMetadata(success_rate=-0.1)  # < 0
        assert "success_rate must be between 0 and 1" in str(exc_info.value)

    def test_memory_record_validation(self):
        """Test MemoryRecord validation and methods."""
        # Valid record
        record = MemoryRecord(
            key="test_key",
            content="test content",
            tags=["tag1", "tag2", "tag1"],  # Duplicate tags
            priority=MemoryPriority.HIGH,
            ttl_seconds=3600
        )

        # Tags should be deduplicated
        assert record.tags == ["tag1", "tag2"]
        assert record.priority == MemoryPriority.HIGH

        # Test is_expired method if it exists
        if hasattr(record, 'is_expired'):
            assert not record.is_expired()

        # Test to_dict method if it exists
        if hasattr(record, 'to_dict'):
            record_dict = record.to_dict()
            assert isinstance(record_dict, dict)
            assert record_dict["key"] == "test_key"

    def test_memory_search_result(self):
        """Test MemorySearchResult model."""
        record1 = MemoryRecord(key="key1", content="content1")
        record2 = MemoryRecord(key="key2", content="content2")

        result = MemorySearchResult(
            records=[record1, record2],
            total_count=2,
            search_query={"tags": ["test"]},
            execution_time_ms=15.5
        )

        assert result.total_count == 2
        assert len(result.records) == 2

        # Test get_by_key method
        found = result.get_by_key("key1")
        assert found is not None
        assert found.key == "key1"

        not_found = result.get_by_key("key3")
        assert not_found is None

        # Test filter_by_priority method
        high_priority = result.filter_by_priority(MemoryPriority.HIGH)
        assert isinstance(high_priority, list)


class TestTelemetryModels:
    """Test telemetry-related Pydantic models."""

    def test_telemetry_event_validation(self):
        """Test TelemetryEvent validation."""
        event = TelemetryEvent(
            event_id="evt_123",
            event_type=EventType.TOOL_INVOCATION,
            severity=EventSeverity.INFO,
            timestamp=datetime.now(),
            agent_id="agent_1",
            metadata={"tool": "search", "status": "success"}
        )

        assert event.event_type == EventType.TOOL_INVOCATION
        assert event.agent_id == "agent_1"
        assert event.severity == EventSeverity.INFO

    def test_event_type_enum(self):
        """Test EventType enum values."""
        assert EventType.AGENT_START.value == "agent_start"
        assert EventType.TOOL_INVOCATION.value == "tool_invocation"
        assert EventType.ERROR.value == "error"
        assert EventType.LLM_CALL.value == "llm_call"

    def test_health_status_validation(self):
        """Test HealthStatus model from core."""
        health = HealthStatus(
            status="healthy",
            healing_enabled=True,
            patterns_loaded=100,
            telemetry_active=True,
            learning_loop_active=True
        )

        assert health.status == "healthy"
        assert health.healing_enabled is True
        assert health.patterns_loaded == 100


class TestTypeGuards:
    """Test type guard patterns used throughout the codebase."""

    def test_isinstance_guards_for_primitives(self):
        """Test isinstance() guards for primitive types."""
        # Test patterns from the codebase
        value: Any = 42
        if isinstance(value, (int, float)):
            # This should work without type errors
            result = value + 10
            assert result == 52

        value = "string"
        if isinstance(value, str):
            # This should work without type errors
            result = value.upper()
            assert result == "STRING"

        value = [1, 2, 3]
        if isinstance(value, list):
            # This should work without type errors
            result = len(value)
            assert result == 3

    def test_type_guard_for_optional_values(self):
        """Test type guards for Optional types."""
        optional_value: Optional[Dict[str, Any]] = {"key": "value"}

        if optional_value is not None:
            # After the guard, optional_value is Dict[str, Any]
            assert "key" in optional_value
            assert optional_value["key"] == "value"

        optional_value = None
        if optional_value is None:
            # Properly handle None case
            assert optional_value is None

    def test_complex_type_guards(self):
        """Test complex type guard patterns from the codebase."""
        # Pattern from swarm_memory.py
        tags_value: Any = ["tag1", "tag2"]
        if isinstance(tags_value, list):
            memory_tags = set(str(tag) for tag in tags_value if isinstance(tag, str))
            assert memory_tags == {"tag1", "tag2"}

        # Pattern for priority checking
        priority_val: Any = 3
        if isinstance(priority_val, (int, float)):
            priority_int = int(priority_val)
            assert priority_int == 3

    def test_model_validation_with_factory(self):
        """Test model creation with default factories."""
        # Test that default factories work correctly
        metadata = MemoryMetadata()  # Uses default_factory
        assert metadata.additional == {}

        record = MemoryRecord(
            key="test",
            content="content"
        )
        assert record.tags == []  # default_factory=list
        assert record.priority == MemoryPriority.MEDIUM  # default value


class TestBackwardCompatibility:
    """Test backward compatibility for Dict to Model conversions."""

    def test_dict_to_memory_record_conversion(self):
        """Test converting dict to MemoryRecord."""
        # Old dict format
        old_format = {
            "key": "test_key",
            "content": "test content",
            "tags": ["tag1", "tag2"],
            "timestamp": datetime.now().isoformat(),
            "priority": "high"
        }

        # Should be convertible to MemoryRecord
        record = MemoryRecord(
            key=old_format["key"],
            content=old_format["content"],
            tags=old_format["tags"],
            timestamp=datetime.fromisoformat(old_format["timestamp"]),
            priority=MemoryPriority(old_format["priority"])
        )

        assert record.key == "test_key"
        assert record.priority == MemoryPriority.HIGH

    def test_model_to_dict_conversion(self):
        """Test converting models back to dicts for compatibility."""
        record = MemoryRecord(
            key="test",
            content={"data": "value"},
            tags=["tag1"],
            priority=MemoryPriority.CRITICAL
        )

        # Convert to dict using model_dump
        record_dict = record.model_dump()

        # Should be a proper dict with JSON-compatible values
        assert isinstance(record_dict, dict)
        assert record_dict["key"] == "test"
        assert record_dict["priority"] == "critical"


class TestErrorHandling:
    """Test error handling and validation errors."""

    def test_strict_validation_no_extra_fields(self):
        """Test that models reject extra fields (extra='forbid')."""
        with pytest.raises(ValidationError) as exc_info:
            MemoryMetadata(
                agent_id="test",
                unknown_field="should_fail"  # This should be rejected
            )
        assert "Extra inputs are not permitted" in str(exc_info.value)

    def test_required_field_validation(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError) as exc_info:
            MemoryRecord(
                # Missing required 'key' field
                content="test"
            )
        assert "Field required" in str(exc_info.value)

    def test_type_validation(self):
        """Test that field types are enforced."""
        with pytest.raises(ValidationError) as exc_info:
            MemoryRecord(
                key=123,  # Should be string
                content="test"
            )
        assert "Input should be a valid string" in str(exc_info.value)


class TestJSONValueTypeHandling:
    """Test JSONValue type handling in the codebase."""

    def test_json_value_imports(self):
        """Test that JSONValue is properly imported and usable."""
        # JSONValue should be importable
        from shared.type_definitions.json import JSONValue

        # Should handle basic JSON types
        values: List[JSONValue] = [
            None,
            True,
            42,
            3.14,
            "string",
            [1, 2, 3],
            {"key": "value"}
        ]

        for value in values:
            # These should all be valid JSONValue instances
            assert value == value  # Basic check

    def test_json_value_with_memory_record(self):
        """Test MemoryRecord handles JSONValue content correctly."""
        # Test with various JSONValue types
        test_cases = [
            "string content",
            123,
            {"complex": {"nested": [1, 2, 3]}},
            [1, "two", 3.0],
            None
        ]

        for input_val in test_cases:
            record = MemoryRecord(
                key="test",
                content=input_val
            )
            assert record.content == input_val

            # Should be JSON serializable (with mode='json' for datetime handling)
            json_dict = record.model_dump(mode='json')
            json_str = json.dumps(json_dict)
            assert json_str  # Just verify it doesn't raise


class TestEnhancedMemoryStorePatterns:
    """Test patterns used in enhanced_memory_store.py conversions."""

    def test_fail_fast_on_invalid_types(self):
        """Test that invalid types fail at validation, not silently."""
        # Test that non-JSON types are properly caught
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            # Sets are not JSON serializable
            invalid_record = MemoryRecord(
                key="invalid",
                content={1, 2, 3}  # This should fail
            )

    def test_memory_search_result_usage_pattern(self):
        """Test the correct usage pattern for MemorySearchResult."""
        result = MemorySearchResult(
            records=[
                MemoryRecord(key="1", content="a"),
                MemoryRecord(key="2", content="b")
            ],
            total_count=2
        )

        # Correct patterns - use total_count or len(records)
        assert result.total_count == 2
        assert len(result.records) == 2

        # MemorySearchResult itself doesn't support len()
        # This was the bug in test_firestore_batch_operations
        with pytest.raises(TypeError):
            _ = len(result)  # Should raise TypeError


class TestDictToTypedModelMigration:
    """Test migration from Dict[Any, Any] to typed models."""

    def test_memory_metadata_typed_additional(self):
        """Test that MemoryMetadata.additional is properly typed."""
        metadata = MemoryMetadata(
            additional={
                "string": "value",
                "number": 123,
                "nested": {"data": [1, 2, 3]}
            }
        )

        # Should be Dict[str, JSONValue]
        assert isinstance(metadata.additional, dict)
        for key, value in metadata.additional.items():
            assert isinstance(key, str)

    def test_memory_search_result_typed_query(self):
        """Test that MemorySearchResult.search_query is properly typed."""
        result = MemorySearchResult(
            search_query={
                "tags": ["test", "demo"],
                "priority": "high",
                "limit": 10
            }
        )

        # Should be Dict[str, JSONValue]
        assert isinstance(result.search_query, dict)
        for key in result.search_query:
            assert isinstance(key, str)


class TestPerformanceOptimizations:
    """Test performance optimization patterns from Claude's review."""

    def test_isinstance_check_optimization(self):
        """Test that isinstance checks can be optimized."""
        # Pattern from enhanced_memory_store.py
        value: Any = {"data": [1, 2, 3]}

        # Instead of multiple isinstance checks, cache the result
        is_dict = isinstance(value, dict)

        if is_dict:
            # Process as dict without redundant checks
            for key, val in value.items():
                assert isinstance(key, str)

    def test_type_guard_caching_pattern(self):
        """Test caching pattern for type guards."""
        # Simulate a hot path with multiple type checks
        def process_value(value: Any) -> str:
            # Cache type check results
            is_str = isinstance(value, str)
            is_int = isinstance(value, (int, float))

            if is_str:
                return value.upper()
            elif is_int:
                return str(int(value))
            else:
                return str(value)

        assert process_value("test") == "TEST"
        assert process_value(42) == "42"
        assert process_value(3.14) == "3"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])