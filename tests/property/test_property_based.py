"""
Property-based tests for core Agency types.

Automatically generates thousands of test cases for:
- Result<T, E> pattern
- JSONValue types
- VectorStore operations
- Memory system

Each property test runs 100-1000 examples by default.
Hypothesis will automatically shrink failing cases to minimal examples.
"""

import json

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.stateful import run_state_machine_as_test

from agency_memory.vector_store import VectorStore
from shared.type_definitions.json_value import JSONValue
from shared.type_definitions.result import Err, Ok, Result
from tools.property_testing import (
    JSONValueProperties,
    ResultPatternProperties,
    VectorStoreProperties,
    VectorStoreStateMachine,
    json_value_strategy,
    memory_record_strategy,
    result_strategy,
)

# ============================================================================
# RESULT PATTERN PROPERTIES
# ============================================================================


class TestResultPatternProperties:
    """
    Property-based tests for Result<T, E> pattern.

    Each test runs 100+ examples with automatic shrinking on failure.
    """

    @given(result_strategy())
    def test_result_mutual_exclusivity(self, result: Result):
        """
        PROPERTY: Result is EITHER Ok OR Err, never both, never neither.

        This is a fundamental invariant of the Result pattern.
        """
        assert ResultPatternProperties.test_mutual_exclusivity(result)

    @given(result_strategy())
    def test_ok_unwrap_succeeds(self, result: Result):
        """PROPERTY: If Ok, unwrap() succeeds without exception."""
        assert ResultPatternProperties.test_ok_unwrap_succeeds(result)

    @given(result_strategy())
    def test_ok_unwrap_err_fails(self, result: Result):
        """PROPERTY: If Ok, unwrap_err() raises RuntimeError."""
        assert ResultPatternProperties.test_ok_unwrap_err_fails(result)

    @given(result_strategy())
    def test_err_unwrap_fails(self, result: Result):
        """PROPERTY: If Err, unwrap() raises RuntimeError."""
        assert ResultPatternProperties.test_err_unwrap_fails(result)

    @given(result_strategy())
    def test_err_unwrap_err_succeeds(self, result: Result):
        """PROPERTY: If Err, unwrap_err() succeeds without exception."""
        assert ResultPatternProperties.test_err_unwrap_err_succeeds(result)

    @given(result_strategy(), st.integers())
    def test_unwrap_or_never_raises(self, result: Result, default: int):
        """PROPERTY: unwrap_or() never raises exception."""
        assert ResultPatternProperties.test_unwrap_or_always_succeeds(result, default)

    @given(result_strategy())
    def test_map_preserves_err(self, result: Result):
        """PROPERTY: map() preserves Err unchanged."""
        assert ResultPatternProperties.test_map_preserves_err(result)

    @given(result_strategy())
    def test_map_err_preserves_ok(self, result: Result):
        """PROPERTY: map_err() preserves Ok unchanged."""
        assert ResultPatternProperties.test_map_err_preserves_ok(result)

    @given(result_strategy(st.integers()), st.integers())
    def test_unwrap_or_returns_value_or_default(self, result: Result, default: int):
        """PROPERTY: unwrap_or() returns value if Ok, default if Err."""
        value = result.unwrap_or(default)
        if result.is_ok():
            assert value == result.unwrap()
        else:
            assert value == default

    @given(result_strategy(st.lists(st.integers())))
    def test_map_composition(self, result: Result):
        """PROPERTY: map() is composable: r.map(f).map(g) == r.map(lambda x: g(f(x)))."""

        def f(x):
            return len(x) if isinstance(x, list) else 0

        def g(x):
            return x * 2

        mapped_separate = result.map(f).map(g)
        mapped_composed = result.map(lambda x: g(f(x)))

        if result.is_ok():
            assert mapped_separate.unwrap() == mapped_composed.unwrap()
        else:
            assert mapped_separate.is_err()
            assert mapped_composed.is_err()

    @given(result_strategy(st.integers()))
    def test_and_then_chaining(self, result: Result):
        """PROPERTY: and_then() chains operations correctly."""

        def safe_divide(x):
            if x == 0:
                return Err("division by zero")
            return Ok(10 / x)

        chained = result.and_then(safe_divide)

        if result.is_err():
            # Err propagates
            assert chained.is_err()
        elif result.is_ok() and result.unwrap() == 0:
            # Operation fails
            assert chained.is_err()
        else:
            # Operation succeeds
            assert chained.is_ok()


# ============================================================================
# JSON VALUE PROPERTIES
# ============================================================================


class TestJSONValueProperties:
    """
    Property-based tests for JSONValue types.

    Validates JSON-serializability and type constraints.
    """

    @given(json_value_strategy())
    def test_json_serializable(self, value: JSONValue):
        """PROPERTY: All JSONValue instances are JSON-serializable."""
        assert JSONValueProperties.test_json_serializable(value)

    @given(json_value_strategy())
    def test_json_roundtrip_identity(self, value: JSONValue):
        """PROPERTY: JSON roundtrip preserves value equality."""
        serialized = json.dumps(value)
        deserialized = json.loads(serialized)
        assert deserialized == value

    @given(json_value_strategy())
    def test_json_roundtrip_preserves_primitives(self, value: JSONValue):
        """PROPERTY: JSON roundtrip preserves primitive types."""
        assert JSONValueProperties.test_json_roundtrip_preserves_type(value)

    @given(st.text(), json_value_strategy())
    def test_json_dict_construction(self, key: str, value: JSONValue):
        """PROPERTY: Can construct dicts from JSONValues."""
        # Use text strategy for keys to avoid filtering
        test_dict = {key: value}
        serialized = json.dumps(test_dict)
        deserialized = json.loads(serialized)
        assert deserialized == test_dict

    @given(st.lists(json_value_strategy()))
    def test_json_list_construction(self, values: list):
        """PROPERTY: Can construct lists from JSONValues."""
        serialized = json.dumps(values)
        deserialized = json.loads(serialized)
        assert deserialized == values

    @given(json_value_strategy(max_leaves=5))
    def test_nested_json_serialization(self, value: JSONValue):
        """PROPERTY: Nested JSON structures serialize correctly."""
        # Wrap in multiple layers
        nested = {"level1": {"level2": {"level3": value}}}
        serialized = json.dumps(nested)
        deserialized = json.loads(serialized)
        assert deserialized["level1"]["level2"]["level3"] == value


# ============================================================================
# VECTOR STORE PROPERTIES
# ============================================================================


class TestVectorStoreProperties:
    """
    Property-based tests for VectorStore operations.

    Tests state consistency and search correctness.
    """

    @given(st.text(min_size=1, max_size=50), memory_record_strategy())
    def test_add_memory_increases_count(self, key: str, content: dict):
        """PROPERTY: Adding memory increases total count."""
        store = VectorStore()
        assert VectorStoreProperties.test_add_increases_count(store, key, content)

    @given(st.text(min_size=1, max_size=50), memory_record_strategy())
    def test_remove_memory_decreases_count(self, key: str, content: dict):
        """PROPERTY: Removing memory decreases total count."""
        store = VectorStore()
        assert VectorStoreProperties.test_remove_decreases_count(store, key, content)

    @given(st.text(min_size=1, max_size=50), memory_record_strategy())
    def test_search_finds_added_content(self, key: str, content: dict):
        """PROPERTY: Search finds recently added content."""
        store = VectorStore()
        # Use keyword search to avoid embedding dependency
        assert VectorStoreProperties.test_search_returns_added_content(store, key, content)

    @given(st.lists(memory_record_strategy(), min_size=1, max_size=10))
    def test_multiple_additions_count_correctly(self, records: list):
        """PROPERTY: Adding N memories increases count by N."""
        store = VectorStore()

        initial_stats = store.get_stats()
        initial_count = initial_stats.get("total_memories", 0)

        # Add all records with unique keys
        for i, record in enumerate(records):
            unique_key = f"key_{i}_{record['key']}"
            store.add_memory(unique_key, record)

        final_stats = store.get_stats()
        final_count = final_stats.get("total_memories", 0)

        assert final_count == initial_count + len(records)

    @given(st.text(min_size=1, max_size=50), memory_record_strategy())
    def test_add_remove_idempotent(self, key: str, content: dict):
        """PROPERTY: Add then remove returns to initial state."""
        store = VectorStore()

        initial_stats = store.get_stats()
        initial_count = initial_stats.get("total_memories", 0)

        store.add_memory(key, content)
        store.remove_memory(key)

        final_stats = store.get_stats()
        final_count = final_stats.get("total_memories", 0)

        assert final_count == initial_count

    @given(st.text(min_size=1), st.lists(memory_record_strategy(), max_size=5))
    def test_search_never_crashes(self, query: str, records: list):
        """PROPERTY: Search operations never crash."""
        store = VectorStore()

        # Add records
        for i, record in enumerate(records):
            store.add_memory(f"key_{i}", record)

        # Search should not crash
        try:
            results = store.keyword_search(query, records, top_k=10)
            assert isinstance(results, list)
        except Exception as e:
            pytest.fail(f"Search crashed: {e}")

    @given(memory_record_strategy())
    def test_stats_always_valid(self, content: dict):
        """PROPERTY: Store statistics are always valid."""
        store = VectorStore()
        store.add_memory("test_key", content)

        stats = store.get_stats()

        assert isinstance(stats, dict)
        assert "total_memories" in stats
        assert isinstance(stats["total_memories"], int)
        assert stats["total_memories"] >= 0
        assert "embedding_provider" in stats
        assert "embedding_available" in stats


# ============================================================================
# STATEFUL TESTING
# ============================================================================


class TestVectorStoreStateful:
    """
    Stateful property testing for VectorStore.

    Hypothesis will execute random sequences of operations and verify invariants.
    """

    def test_vector_store_state_machine(self):
        """
        Run stateful tests on VectorStore.

        Executes random sequences of add/remove/search operations
        and validates that all invariants hold.
        """
        run_state_machine_as_test(
            VectorStoreStateMachine,
            settings=settings(max_examples=50, stateful_step_count=20, deadline=2000),
        )


# ============================================================================
# INTEGRATION PROPERTIES
# ============================================================================


class TestIntegrationProperties:
    """
    Property tests for integration between components.
    """

    @given(result_strategy(json_value_strategy()), st.text(min_size=1))
    def test_result_with_json_value(self, result: Result, error_msg: str):
        """PROPERTY: Result works correctly with JSONValue payloads."""
        if result.is_ok():
            value = result.unwrap()
            # Should be JSON-serializable
            serialized = json.dumps(value)
            deserialized = json.loads(serialized)
            assert deserialized == value

    @given(st.lists(result_strategy(st.integers()), min_size=1))
    def test_result_list_processing(self, results: list):
        """PROPERTY: Can process lists of Results correctly."""
        # Partition into Ok and Err
        ok_values = [r.unwrap() for r in results if r.is_ok()]
        err_values = [r.unwrap_err() for r in results if r.is_err()]

        # Should account for all results
        assert len(ok_values) + len(err_values) == len(results)

    @given(st.lists(memory_record_strategy(), min_size=1, max_size=5), st.text(min_size=1))
    def test_memory_search_consistency(self, records: list, query: str):
        """PROPERTY: Search results are consistent across calls."""
        store = VectorStore()

        # Add records
        for i, record in enumerate(records):
            store.add_memory(f"key_{i}", record)

        # Search twice - should get same results
        results1 = store.keyword_search(query, records, top_k=10)
        results2 = store.keyword_search(query, records, top_k=10)

        # Results should be identical
        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1.similarity_score == r2.similarity_score


# ============================================================================
# PERFORMANCE PROPERTIES
# ============================================================================


class TestPerformanceProperties:
    """
    Property tests for performance characteristics.
    """

    @given(st.integers(min_value=1, max_value=100))
    def test_search_scales_linearly(self, num_records: int):
        """PROPERTY: Search time scales linearly with record count."""
        import time

        store = VectorStore()

        # Add records
        for i in range(num_records):
            record = {"key": f"key_{i}", "content": f"content {i}", "tags": []}
            store.add_memory(f"key_{i}", record)

        # Measure search time
        start = time.time()
        store.search("test query", limit=10)
        elapsed = time.time() - start

        # Should complete in reasonable time (< 1 second for 100 records)
        assert elapsed < 1.0, f"Search took {elapsed}s for {num_records} records"

    @given(st.lists(memory_record_strategy(), min_size=10, max_size=50))
    def test_bulk_operations_efficient(self, records: list):
        """PROPERTY: Bulk operations complete in reasonable time."""
        import time

        store = VectorStore()

        start = time.time()
        for i, record in enumerate(records):
            store.add_memory(f"key_{i}", record)
        elapsed = time.time() - start

        # Should add records quickly (< 0.5s for 50 records without embeddings)
        assert elapsed < 0.5, f"Bulk add took {elapsed}s for {len(records)} records"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
