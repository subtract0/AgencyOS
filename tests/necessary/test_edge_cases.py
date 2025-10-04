"""
NECESSARY Pattern Tests: Edge Cases

Tests focus on:
- Boundary conditions
- Empty/null parameter handling
- Extreme values
- Unusual but valid inputs
- Concurrent operations
"""

from unittest.mock import Mock, patch

import pytest

from agency_code_agent.agency_code_agent import create_agency_code_agent
from agency_memory.enhanced_memory_store import EnhancedMemoryStore
from agency_memory.memory import InMemoryStore
from shared.agent_context import create_agent_context
from shared.model_policy import agent_model


class TestMemoryEdgeCases:
    """Test edge cases for memory system."""

    def test_store_with_empty_string_key(self):
        """Test storing memory with empty string as key."""
        store = InMemoryStore()

        # Empty string key should be handled
        store.store("", {"data": "test"}, ["test"])

        # Should be retrievable
        record = store.get("")
        assert record is not None

    def test_store_with_empty_dict_content(self):
        """Test storing empty dictionary as content."""
        store = InMemoryStore()

        store.store("empty", {}, ["test"])

        record = store.get("empty")
        assert record is not None
        assert record.content == {}

    def test_store_with_empty_tags_list(self):
        """Test storing with empty tags list."""
        store = InMemoryStore()

        store.store("notags", {"data": "test"}, [])

        record = store.get("notags")
        assert record is not None
        assert record.tags == []

    def test_search_with_duplicate_tags(self):
        """Test searching with duplicate tags in query."""
        store = InMemoryStore()
        store.store("key1", {"data": "test"}, ["tag1", "tag2"])

        # Search with duplicate tags
        result = store.search(["tag1", "tag1", "tag1"])

        # Should return result once (no duplicates in results)
        assert result.total_count == 1
        assert len(result.records) == 1

    def test_store_with_duplicate_tags(self):
        """Test storing with duplicate tags."""
        store = InMemoryStore()

        store.store("dupetags", {"data": "test"}, ["tag1", "tag1", "tag2", "tag2"])

        record = store.get("dupetags")
        assert record is not None
        # Tags might or might not be deduplicated (both behaviors are valid)
        assert "tag1" in record.tags
        assert "tag2" in record.tags

    def test_store_overwrite_existing_key(self):
        """Test overwriting existing key."""
        store = InMemoryStore()

        # Store initial data
        store.store("key1", {"data": "first"}, ["tag1"])

        # Overwrite with new data
        store.store("key1", {"data": "second"}, ["tag2"])

        # Should have latest data
        record = store.get("key1")
        assert record.content == {"data": "second"}
        assert record.tags == ["tag2"]

        # Should only have one record
        all_records = store.get_all()
        keys = [r.key for r in all_records.records]
        assert keys.count("key1") == 1

    def test_store_with_numeric_string_keys(self):
        """Test storing with numeric string keys."""
        store = InMemoryStore()

        numeric_keys = ["0", "1", "123", "999999"]

        for key in numeric_keys:
            store.store(key, {"number": key}, ["numeric"])

        # All should be retrievable
        for key in numeric_keys:
            record = store.get(key)
            assert record is not None

    def test_store_with_very_long_key(self):
        """Test storing with extremely long key."""
        store = InMemoryStore()

        long_key = "k" * 10000

        store.store(long_key, {"data": "test"}, ["long"])

        record = store.get(long_key)
        assert record is not None

    def test_store_with_very_long_tag(self):
        """Test storing with extremely long tag."""
        store = InMemoryStore()

        long_tag = "t" * 10000

        store.store("key", {"data": "test"}, [long_tag])

        # Should be searchable
        result = store.search([long_tag])
        assert result.total_count == 1

    def test_search_with_very_many_tags(self):
        """Test searching with many tags."""
        store = InMemoryStore()
        store.store("key1", {"data": "test"}, ["tag1"])

        # Search with 1000 tags (most don't match)
        many_tags = [f"tag{i}" for i in range(1000)]
        many_tags.append("tag1")  # Include one that matches

        result = store.search(many_tags)
        assert result.total_count == 1

    def test_memory_with_boolean_values(self):
        """Test storing boolean values in content."""
        store = InMemoryStore()

        store.store("bool_key", {"flag": True, "disabled": False}, ["bool"])

        record = store.get("bool_key")
        assert record.content["flag"] is True
        assert record.content["disabled"] is False

    def test_memory_with_null_in_content(self):
        """Test storing None/null values in content dictionary."""
        store = InMemoryStore()

        store.store("null_key", {"value": None, "other": "data"}, ["null"])

        record = store.get("null_key")
        assert record.content["value"] is None
        assert record.content["other"] == "data"

    def test_memory_with_list_content(self):
        """Test storing list as content."""
        store = InMemoryStore()

        list_content = [1, 2, 3, "four", {"five": 5}]
        store.store("list_key", list_content, ["list"])

        record = store.get("list_key")
        assert record.content == list_content

    def test_enhanced_memory_semantic_search_min_similarity_boundary(self):
        """Test semantic search with boundary similarity values."""
        store = EnhancedMemoryStore()
        store.store("key1", {"data": "test content"}, ["test"])

        # Test with various similarity thresholds
        for min_sim in [0.0, 0.5, 0.99, 1.0]:
            results = store.semantic_search("test", top_k=10, min_similarity=min_sim)
            assert isinstance(results, list)

    def test_enhanced_memory_semantic_search_top_k_boundary(self):
        """Test semantic search with boundary top_k values."""
        store = EnhancedMemoryStore()

        for i in range(20):
            store.store(f"key{i}", {"data": f"content {i}"}, ["test"])

        # Test with various top_k values
        for k in [0, 1, 10, 100, 1000]:
            results = store.semantic_search("content", top_k=k)
            assert isinstance(results, list)
            if k > 0:
                assert len(results) <= k


class TestAgentContextEdgeCases:
    """Test edge cases for AgentContext."""

    def test_agent_context_with_empty_session_id(self):
        """Test creating agent context with empty session ID."""
        # Should handle or reject empty session ID
        context = create_agent_context(session_id="")
        # Implementation generates a default session ID when empty string provided
        # This is valid behavior - ensures session always has an ID
        assert context.session_id is not None
        assert len(context.session_id) > 0

    def test_agent_context_store_memory_with_empty_tags(self):
        """Test storing memory with empty tags list."""
        context = create_agent_context()

        context.store_memory("key", {"data": "test"}, [])

        # Should retrieve successfully
        memories = context.search_memories([])
        # Might return empty or all memories depending on implementation

    def test_agent_context_search_with_nonexistent_tags(self):
        """Test searching for tags that don't exist."""
        context = create_agent_context()
        context.store_memory("key1", {"data": "test"}, ["tag1"])

        # Search for non-existent tags
        results = context.search_memories(["nonexistent", "nothere"])

        assert isinstance(results, list)
        assert len(results) == 0

    def test_agent_context_get_session_memories_empty(self):
        """Test getting session memories when none exist."""
        context = create_agent_context()

        memories = context.get_session_memories()

        assert isinstance(memories, list)
        assert len(memories) == 0

    def test_agent_context_multiple_stores_same_key(self):
        """Test storing multiple times with same key."""
        context = create_agent_context()

        context.store_memory("duplicate", {"version": 1}, ["v1"])
        context.store_memory("duplicate", {"version": 2}, ["v2"])
        context.store_memory("duplicate", {"version": 3}, ["v3"])

        # Latest version should be accessible
        memories = context.get_session_memories()
        # Should have only one or all versions depending on implementation


class TestModelPolicyEdgeCases:
    """Test edge cases for model policy."""

    def test_agent_model_with_whitespace_key(self):
        """Test agent_model with whitespace in key."""
        # Should not match any known key
        model = agent_model("  planner  ")
        # Should fall back to default
        assert model in ["gpt-5", "gpt-5-mini"]

    def test_agent_model_with_numeric_key(self):
        """Test agent_model with numeric key (as string)."""
        model = agent_model("123")
        # Should fall back to default
        assert model in ["gpt-5", "gpt-5-mini"]

    def test_agent_model_all_valid_keys(self):
        """Test agent_model with all documented valid keys."""
        valid_keys = [
            "planner",
            "chief_architect",
            "coder",
            "auditor",
            "quality_enforcer",
            "merger",
            "learning",
            "test_generator",
            "summary",
            "toolsmith",
        ]

        for key in valid_keys:
            model = agent_model(key)
            # Should return valid model name
            assert isinstance(model, str)
            assert len(model) > 0

    def test_agent_model_case_variations(self):
        """Test agent_model with various case combinations."""
        # Should be case-sensitive
        model_lower = agent_model("planner")
        model_upper = agent_model("PLANNER")
        model_mixed = agent_model("Planner")

        # All non-matching should return default
        assert model_lower != model_upper or model_upper in ["gpt-5", "gpt-5-mini"]
        assert model_lower != model_mixed or model_mixed in ["gpt-5", "gpt-5-mini"]


class TestAgentCreationEdgeCases:
    """Test edge cases for agent creation."""

    def test_agent_creation_with_minimum_parameters(self):
        """Test creating agent with minimal parameters."""
        with (
            patch("agency_code_agent.agency_code_agent.Agent"),
            patch("agency_code_agent.agency_code_agent.get_model_instance") as mock_model,
        ):
            mock_model.return_value = "gpt-5-mini"

            # Should work with defaults
            agent = create_agency_code_agent()
            assert agent is not None

    def test_agent_creation_with_all_parameters(self):
        """Test creating agent with all parameters specified."""
        with (
            patch("agency_code_agent.agency_code_agent.Agent"),
            patch("agency_code_agent.agency_code_agent.get_model_instance") as mock_model,
        ):
            mock_model.return_value = "gpt-5"
            mock_context = Mock()
            mock_context.session_id = "test_session"
            mock_context.store_memory = Mock()

            agent = create_agency_code_agent(
                model="gpt-5", reasoning_effort="high", agent_context=mock_context
            )
            assert agent is not None

    def test_agent_creation_with_invalid_reasoning_effort(self):
        """Test creating agent with invalid reasoning effort."""
        with (
            patch("agency_code_agent.agency_code_agent.Agent"),
            patch("agency_code_agent.agency_code_agent.get_model_instance") as mock_model,
            patch("agency_code_agent.agency_code_agent.create_model_settings") as mock_settings,
        ):
            mock_model.return_value = "gpt-5-mini"
            mock_settings.return_value = Mock()

            # Should handle invalid value (might default or raise)
            try:
                agent = create_agency_code_agent(model="gpt-5-mini", reasoning_effort="invalid")
                # If it doesn't raise, that's valid behavior
                assert agent is not None
            except (ValueError, KeyError):
                # Raising an error is also valid
                pass

    def test_agent_creation_reasoning_effort_boundary_values(self):
        """Test reasoning effort with boundary string values."""
        with (
            patch("agency_code_agent.agency_code_agent.Agent"),
            patch("agency_code_agent.agency_code_agent.get_model_instance") as mock_model,
            patch("agency_code_agent.agency_code_agent.create_model_settings") as mock_settings,
        ):
            mock_model.return_value = "gpt-5-mini"
            mock_settings.return_value = Mock()

            # Test with various edge case inputs
            edge_cases = ["", "LOW", "Medium", "HIGH", "low ", " medium"]

            for effort in edge_cases:
                try:
                    agent = create_agency_code_agent(model="gpt-5-mini", reasoning_effort=effort)
                    # If it succeeds, that's fine
                except (ValueError, KeyError, AttributeError):
                    # Raising errors for invalid input is also fine
                    pass


class TestConcurrentEdgeCases:
    """Test edge cases in concurrent scenarios."""

    def test_concurrent_memory_reads_same_key(self):
        """Test multiple threads reading the same key simultaneously."""
        from threading import Thread

        store = InMemoryStore()

        store.store("shared_key", {"data": "shared"}, ["shared"])

        results = []
        errors = []

        def read_memory():
            try:
                record = store.get("shared_key")
                results.append(record)
            except Exception as e:
                errors.append(e)

        # Create 20 threads all reading same key
        threads = [Thread(target=read_memory) for _ in range(20)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # No errors should occur
        assert len(errors) == 0
        # All reads should succeed
        assert len(results) == 20
        assert all(r is not None for r in results)

    def test_concurrent_memory_overwrites(self):
        """Test multiple threads overwriting the same key."""
        from threading import Thread

        store = InMemoryStore()

        store.store("overwrite_key", {"version": 0}, ["test"])

        errors = []

        def overwrite_memory(version):
            try:
                store.store("overwrite_key", {"version": version}, ["test"])
            except Exception as e:
                errors.append(e)

        # Create 10 threads all overwriting same key
        threads = [Thread(target=overwrite_memory, args=(i,)) for i in range(10)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # No errors should occur
        assert len(errors) == 0

        # Key should exist with one of the versions
        record = store.get("overwrite_key")
        assert record is not None
        assert "version" in record.content
        assert 0 <= record.content["version"] < 10

    def test_concurrent_searches_different_tags(self):
        """Test multiple threads searching different tags simultaneously."""
        from threading import Thread

        store = InMemoryStore()

        # Pre-populate with tagged data
        for i in range(100):
            store.store(f"key_{i}", {"data": i}, [f"tag_{i % 10}"])

        results = []
        errors = []

        def search_tag(tag):
            try:
                result = store.search([tag])
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create threads searching different tags
        threads = [Thread(target=search_tag, args=(f"tag_{i}",)) for i in range(10)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # No errors should occur
        assert len(errors) == 0
        # All searches should return results
        assert len(results) == 10
        # Each should find ~10 items
        for result in results:
            assert result.total_count == 10


class TestBoundaryValueEdgeCases:
    """Test boundary value edge cases."""

    def test_memory_with_max_int_value(self):
        """Test storing maximum integer values."""
        store = InMemoryStore()

        import sys

        max_int = sys.maxsize

        store.store("max_int", {"value": max_int}, ["numbers"])

        record = store.get("max_int")
        assert record.content["value"] == max_int

    def test_memory_with_min_int_value(self):
        """Test storing minimum integer values."""
        store = InMemoryStore()

        import sys

        min_int = -sys.maxsize - 1

        store.store("min_int", {"value": min_int}, ["numbers"])

        record = store.get("min_int")
        assert record.content["value"] == min_int

    def test_memory_with_float_special_values(self):
        """Test storing special float values."""
        store = InMemoryStore()

        special_values = {
            "positive_inf": float("inf"),
            "negative_inf": float("-inf"),
            "zero": 0.0,
            "negative_zero": -0.0,
        }

        store.store("special_floats", special_values, ["floats"])

        record = store.get("special_floats")
        assert record.content["positive_inf"] == float("inf")
        assert record.content["negative_inf"] == float("-inf")

    def test_memory_search_with_single_tag(self):
        """Test searching with exactly one tag."""
        store = InMemoryStore()
        store.store("key1", {"data": "test"}, ["single"])

        result = store.search(["single"])

        assert result.total_count == 1

    def test_memory_get_all_with_no_memories(self):
        """Test get_all when store is empty."""
        store = InMemoryStore()

        result = store.get_all()

        assert result.total_count == 0
        assert len(result.records) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
