"""
Property-Based Testing Framework for Agency OS.

Provides Hypothesis-based property testing with custom strategies for Agency types.
Auto-generates thousands of test cases to verify invariants and properties.

Constitutional Compliance:
- TDD-first: Tests define expected properties
- Strict typing: All strategies are type-safe
- Result pattern: Error handling via Result<T, E>
- No Dict[Any, Any]: Uses Pydantic models

Example:
    from tools.property_testing import result_strategy, PropertyTests
    from hypothesis import given

    @given(result_strategy())
    def test_result_invariants(result):
        # Properties that ALWAYS hold for Result instances
        assert result.is_ok() != result.is_err()
"""

import logging
from collections.abc import Callable
from typing import Any, TypeVar

from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from shared.type_definitions.json_value import JSONValue
from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)

T = TypeVar("T")
E = TypeVar("E")


# ============================================================================
# CUSTOM STRATEGIES FOR AGENCY TYPES
# ============================================================================


@st.composite
def result_strategy(draw, value_strategy=st.integers(), error_strategy=st.text(min_size=1)):
    """
    Generate Result<T, E> values for property testing.

    Args:
        draw: Hypothesis draw function
        value_strategy: Strategy for Ok values (default: integers)
        error_strategy: Strategy for Err values (default: non-empty text)

    Returns:
        Result instance (Ok or Err)

    Example:
        @given(result_strategy(st.lists(st.integers())))
        def test_result_with_lists(result):
            assert result.is_ok() or result.is_err()
    """
    is_ok = draw(st.booleans())
    if is_ok:
        value = draw(value_strategy)
        return Ok(value)
    else:
        error = draw(error_strategy)
        return Err(error)


@st.composite
def json_value_strategy(draw, max_leaves=10):
    """
    Generate valid JSONValue instances for property testing.

    Generates recursive JSON structures: primitives, lists, and dicts.
    Ensures all values are JSON-serializable.

    Args:
        draw: Hypothesis draw function
        max_leaves: Maximum leaf nodes in recursive structures

    Returns:
        JSONValue instance

    Example:
        @given(json_value_strategy())
        def test_json_serialization(value):
            import json
            assert json.loads(json.dumps(value)) == value
    """
    return draw(
        st.recursive(
            st.one_of(
                st.none(),
                st.booleans(),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text(),
            ),
            lambda children: st.one_of(st.lists(children), st.dictionaries(st.text(), children)),
            max_leaves=max_leaves,
        )
    )


@st.composite
def memory_record_strategy(draw):
    """
    Generate memory record structures for VectorStore testing.

    Returns:
        Dict with key, content, tags, and metadata
    """
    return {
        "key": draw(st.text(min_size=1, max_size=50)),
        "content": draw(st.text(min_size=0, max_size=500)),
        "tags": draw(st.lists(st.text(min_size=1, max_size=20), max_size=10)),
        "metadata": draw(
            st.dictionaries(st.text(min_size=1, max_size=20), st.text(max_size=100), max_size=5)
        ),
    }


@st.composite
def agent_context_strategy(draw):
    """
    Generate AgentContext-compatible data.

    Returns:
        Dict with session_id and metadata
    """
    return {
        "session_id": draw(st.text(min_size=10, max_size=100)),
        "metadata": draw(st.dictionaries(st.text(min_size=1), json_value_strategy(), max_size=10)),
    }


# ============================================================================
# PROPERTY TEST COLLECTIONS
# ============================================================================


class ResultPatternProperties:
    """
    Property-based tests for Result<T, E> pattern.

    Validates fundamental invariants that MUST hold for all Result instances.
    """

    @staticmethod
    def test_mutual_exclusivity(result: Result) -> bool:
        """Result is EITHER Ok OR Err, never both, never neither."""
        return result.is_ok() != result.is_err()

    @staticmethod
    def test_ok_unwrap_succeeds(result: Result) -> bool:
        """If Ok, unwrap() returns value without exception."""
        if result.is_ok():
            try:
                result.unwrap()
                return True
            except Exception:
                return False
        return True

    @staticmethod
    def test_ok_unwrap_err_fails(result: Result) -> bool:
        """If Ok, unwrap_err() raises exception."""
        if result.is_ok():
            try:
                result.unwrap_err()
                return False  # Should have raised
            except RuntimeError:
                return True
            except Exception:
                return False
        return True

    @staticmethod
    def test_err_unwrap_fails(result: Result) -> bool:
        """If Err, unwrap() raises exception."""
        if result.is_err():
            try:
                result.unwrap()
                return False  # Should have raised
            except RuntimeError:
                return True
            except Exception:
                return False
        return True

    @staticmethod
    def test_err_unwrap_err_succeeds(result: Result) -> bool:
        """If Err, unwrap_err() returns error without exception."""
        if result.is_err():
            try:
                result.unwrap_err()
                return True
            except Exception:
                return False
        return True

    @staticmethod
    def test_unwrap_or_always_succeeds(result: Result, default: Any) -> bool:
        """unwrap_or() never raises exception."""
        try:
            result.unwrap_or(default)
            return True
        except Exception:
            return False

    @staticmethod
    def test_map_preserves_err(result: Result) -> bool:
        """map() preserves Err unchanged."""
        if result.is_err():
            original_error = result.unwrap_err()
            mapped = result.map(lambda x: x)
            return mapped.is_err() and mapped.unwrap_err() == original_error
        return True

    @staticmethod
    def test_map_err_preserves_ok(result: Result) -> bool:
        """map_err() preserves Ok unchanged."""
        if result.is_ok():
            original_value = result.unwrap()
            mapped = result.map_err(lambda e: e)
            return mapped.is_ok() and mapped.unwrap() == original_value
        return True


class JSONValueProperties:
    """
    Property-based tests for JSONValue types.

    Validates JSON-serializability and type constraints.
    """

    @staticmethod
    def test_json_serializable(value: JSONValue) -> bool:
        """All JSONValue instances must be JSON-serializable."""
        import json

        try:
            serialized = json.dumps(value)
            deserialized = json.loads(serialized)
            return deserialized == value
        except Exception:
            return False

    @staticmethod
    def test_json_roundtrip_preserves_type(value: JSONValue) -> bool:
        """JSON roundtrip preserves primitive types."""
        import json

        try:
            serialized = json.dumps(value)
            deserialized = json.loads(serialized)
            # Type preservation for primitives
            if value is None:
                return deserialized is None
            if isinstance(value, bool):
                return isinstance(deserialized, bool)
            if isinstance(value, int) and not isinstance(value, bool):
                return isinstance(deserialized, int)
            if isinstance(value, str):
                return isinstance(deserialized, str)
            return True
        except Exception:
            return False


class VectorStoreProperties:
    """
    Property-based tests for VectorStore operations.

    Validates state consistency and search correctness.
    """

    @staticmethod
    def test_add_increases_count(store, key: str, content: dict) -> bool:
        """Adding memory increases total count."""
        initial_stats = store.get_stats()
        initial_count = initial_stats.get("total_memories", 0)

        store.add_memory(key, content)

        final_stats = store.get_stats()
        final_count = final_stats.get("total_memories", 0)

        return final_count == initial_count + 1

    @staticmethod
    def test_remove_decreases_count(store, key: str, content: dict) -> bool:
        """Removing memory decreases total count."""
        store.add_memory(key, content)

        stats_before = store.get_stats()
        count_before = stats_before.get("total_memories", 0)

        store.remove_memory(key)

        stats_after = store.get_stats()
        count_after = stats_after.get("total_memories", 0)

        return count_after == count_before - 1

    @staticmethod
    def test_search_returns_added_content(store, key: str, content: dict) -> bool:
        """Search can find recently added content."""
        # Ensure content has the key for searchability
        searchable_content = {**content, "key": key}
        store.add_memory(key, searchable_content)

        # Search by key
        results = store.keyword_search(key, [searchable_content], top_k=10)

        # Should find at least one result if key is non-empty
        if key.strip():
            return len(results) > 0
        return True  # Empty keys might not be searchable


# ============================================================================
# STATEFUL TESTING
# ============================================================================


class VectorStoreStateMachine(RuleBasedStateMachine):
    """
    Stateful property testing for VectorStore.

    Executes random sequences of operations and validates invariants.
    Hypothesis will explore many different execution paths automatically.
    """

    def __init__(self):
        super().__init__()
        from agency_memory.vector_store import VectorStore

        self.store = VectorStore()
        self.added_keys = set()
        self.removed_keys = set()

    @rule(key=st.text(min_size=1, max_size=50), content=st.text())
    def add_memory(self, key, content):
        """Add memory - should always succeed for valid inputs."""
        memory_record = {"key": key, "content": content, "tags": [], "metadata": {}}

        self.store.add_memory(key, memory_record)
        self.added_keys.add(key)
        self.removed_keys.discard(key)

    @rule(key=st.text(min_size=1, max_size=50))
    def remove_memory(self, key):
        """Remove memory - should handle non-existent keys gracefully."""
        self.store.remove_memory(key)
        self.removed_keys.add(key)
        self.added_keys.discard(key)

    @rule(query=st.text(min_size=1))
    def search_memory(self, query):
        """Search should never crash."""
        try:
            results = self.store.search(query)
            assert isinstance(results, list)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    @invariant()
    def stats_are_consistent(self):
        """Store statistics should always be consistent."""
        stats = self.store.get_stats()

        assert isinstance(stats, dict)
        assert "total_memories" in stats
        assert isinstance(stats["total_memories"], int)
        assert stats["total_memories"] >= 0

    @invariant()
    def added_keys_trackable(self):
        """Should be able to track what we've added."""
        # Stats should reflect our tracking (accounting for duplicates)
        stats = self.store.get_stats()
        # Can't be more memories than unique keys we've added
        current_keys = self.added_keys - self.removed_keys
        # Allow for some flexibility due to duplicate adds
        assert stats["total_memories"] <= len(self.added_keys)


# ============================================================================
# SHRINKING HELPERS
# ============================================================================


class MinimalFailureReporter:
    """
    Helper to analyze and report minimal failing cases from Hypothesis.

    When a property test fails, Hypothesis automatically shrinks the input
    to find the simplest case that still fails. This class helps analyze those.
    """

    @staticmethod
    def report_failure(test_name: str, minimal_input: Any, exception: Exception):
        """
        Report minimal failing case for debugging.

        Args:
            test_name: Name of failed test
            minimal_input: Minimal input that causes failure
            exception: Exception raised
        """
        logger.error(f"Property test failed: {test_name}")
        logger.error(f"Minimal failing input: {minimal_input}")
        logger.error(f"Exception: {exception}")

        # Additional analysis
        if isinstance(minimal_input, (list, tuple)):
            logger.error(f"Input length: {len(minimal_input)}")
            if minimal_input:
                logger.error(f"First element: {minimal_input[0]}")

        if isinstance(minimal_input, dict):
            logger.error(f"Keys: {list(minimal_input.keys())}")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def run_property_test(test_func: Callable, strategy, examples: int = 100, max_examples: int = 1000):
    """
    Run a property test with custom configuration.

    Args:
        test_func: Test function to run
        strategy: Hypothesis strategy for input generation
        examples: Minimum number of examples to test
        max_examples: Maximum number of examples

    Example:
        def my_property(x):
            return x == x

        run_property_test(my_property, st.integers(), examples=1000)
    """
    from hypothesis import given, settings

    decorated_test = given(strategy)(test_func)
    configured_test = settings(
        max_examples=max_examples,
        deadline=None,  # No timeout for complex operations
    )(decorated_test)

    configured_test()


def verify_all_properties(properties_class, strategy, examples: int = 100):
    """
    Run all property tests in a properties class.

    Args:
        properties_class: Class containing static property test methods
        strategy: Hypothesis strategy for input generation
        examples: Number of examples to test

    Returns:
        Dict with test results
    """
    from hypothesis import given, settings

    results = {}

    for method_name in dir(properties_class):
        if method_name.startswith("test_"):
            method = getattr(properties_class, method_name)

            try:
                # Run property test
                test_func = given(strategy)(method)
                configured_test = settings(max_examples=examples)(test_func)
                configured_test()

                results[method_name] = "PASS"
                logger.info(f"✓ {method_name}")

            except Exception as e:
                results[method_name] = f"FAIL: {str(e)}"
                logger.error(f"✗ {method_name}: {e}")

    return results


__all__ = [
    # Strategies
    "result_strategy",
    "json_value_strategy",
    "memory_record_strategy",
    "agent_context_strategy",
    # Property test classes
    "ResultPatternProperties",
    "JSONValueProperties",
    "VectorStoreProperties",
    # Stateful testing
    "VectorStoreStateMachine",
    # Helpers
    "MinimalFailureReporter",
    "run_property_test",
    "verify_all_properties",
]
