"""
NECESSARY Pattern Tests: Regression Prevention

Tests focus on:
- Performance benchmarks (agent creation time, memory operations)
- Tool list consistency across versions
- Backwards compatibility (AgentContext, Memory API)
- Data structure stability
- Configuration consistency
"""

import pytest
import time
from unittest.mock import Mock, patch
from agency_memory.memory import InMemoryStore, Memory
from agency_memory.enhanced_memory_store import EnhancedMemoryStore
from shared.agent_context import AgentContext, create_agent_context
from shared.model_policy import agent_model, DEFAULTS
from agency_code_agent.agency_code_agent import create_agency_code_agent


class TestPerformanceBenchmarks:
    """Test performance benchmarks to detect regressions."""

    def test_agent_creation_performance(self):
        """Test that agent creation completes within reasonable time."""
        with patch('agency_code_agent.agency_code_agent.Agent'), \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5-mini"

            start_time = time.time()

            # Create agent
            agent = create_agency_code_agent(
                model="gpt-5-mini",
                reasoning_effort="medium"
            )

            elapsed = time.time() - start_time

            # Agent creation should complete in < 2 seconds
            assert elapsed < 2.0, f"Agent creation took {elapsed:.2f}s, expected < 2.0s"
            assert agent is not None

    def test_memory_store_performance_single_operation(self):
        """Test single memory store operation performance."""
        store = InMemoryStore()

        start_time = time.time()
        store.store("perf_key", {"data": "test"}, ["perf"])
        elapsed = time.time() - start_time

        # Single store should be < 10ms
        assert elapsed < 0.01, f"Store took {elapsed*1000:.2f}ms, expected < 10ms"

    def test_memory_store_performance_batch(self):
        """Test batch memory store operations performance."""
        store = InMemoryStore()

        start_time = time.time()

        # Store 1000 items
        for i in range(1000):
            store.store(f"key_{i}", {"index": i}, [f"tag_{i % 10}"])

        elapsed = time.time() - start_time

        # 1000 stores should complete in < 1 second
        assert elapsed < 1.0, f"Batch store took {elapsed:.2f}s, expected < 1.0s"

    def test_memory_search_performance(self):
        """Test memory search performance."""
        store = InMemoryStore()

        # Pre-populate with 1000 items
        for i in range(1000):
            store.store(f"key_{i}", {"index": i}, [f"tag_{i % 10}"])

        start_time = time.time()

        # Perform search
        result = store.search(["tag_5"])

        elapsed = time.time() - start_time

        # Search should complete in < 50ms
        assert elapsed < 0.05, f"Search took {elapsed*1000:.2f}ms, expected < 50ms"
        assert result.total_count == 100  # Every 10th item

    def test_memory_get_all_performance(self):
        """Test get_all performance with moderate dataset."""
        store = InMemoryStore()

        # Pre-populate with 500 items
        for i in range(500):
            store.store(f"key_{i}", {"index": i}, ["all"])

        start_time = time.time()

        # Get all memories
        result = store.get_all()

        elapsed = time.time() - start_time

        # get_all should complete in < 100ms
        assert elapsed < 0.1, f"get_all took {elapsed*1000:.2f}ms, expected < 100ms"
        assert result.total_count == 500

    def test_agent_context_creation_performance(self):
        """Test AgentContext creation performance."""
        start_time = time.time()

        context = create_agent_context()

        elapsed = time.time() - start_time

        # Context creation should be < 100ms
        assert elapsed < 0.1, f"Context creation took {elapsed*1000:.2f}ms, expected < 100ms"
        assert context is not None

    def test_enhanced_memory_store_performance(self):
        """Test EnhancedMemoryStore operations performance."""
        # Skip VectorStore for performance test
        with patch('agency_memory.enhanced_memory_store.VectorStore'):
            store = EnhancedMemoryStore()

            start_time = time.time()

            # Store 100 items
            for i in range(100):
                store.store(f"key_{i}", {"index": i}, ["perf"])

            elapsed = time.time() - start_time

            # Should complete in < 1 second
            assert elapsed < 1.0, f"Enhanced store took {elapsed:.2f}s, expected < 1.0s"


class TestToolListConsistency:
    """Test tool list consistency to detect regressions."""

    def test_expected_tools_present(self):
        """Test that expected tools are present in agent creation."""
        with patch('agency_code_agent.agency_code_agent.Agent') as mock_agent, \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5-mini"

            create_agency_code_agent(model="gpt-5-mini")

            # Get tools list from agent creation
            call_kwargs = mock_agent.call_args[1]
            tools = call_kwargs.get('tools', [])

            # Verify tools is a non-empty list
            assert isinstance(tools, list)
            assert len(tools) > 0

    def test_tool_list_not_empty(self):
        """Test that tool list is never empty."""
        with patch('agency_code_agent.agency_code_agent.Agent') as mock_agent, \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5-mini"

            # Test with different reasoning efforts
            for effort in ["low", "medium", "high"]:
                create_agency_code_agent(
                    model="gpt-5-mini",
                    reasoning_effort=effort
                )

                call_kwargs = mock_agent.call_args[1]
                tools = call_kwargs.get('tools', [])

                assert len(tools) > 0, f"Tool list empty for reasoning_effort={effort}"

    def test_tool_list_structure_consistency(self):
        """Test that tool list structure is consistent."""
        with patch('agency_code_agent.agency_code_agent.Agent') as mock_agent, \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5-mini"

            create_agency_code_agent()

            call_kwargs = mock_agent.call_args[1]
            tools = call_kwargs.get('tools', [])

            # All tools should be objects/dicts/callables, not primitives
            for tool in tools:
                assert not isinstance(tool, (str, int, float, bool))


class TestBackwardsCompatibility:
    """Test backwards compatibility of APIs."""

    def test_memory_store_interface_compatibility(self):
        """Test that Memory store interface remains compatible."""
        # Basic interface
        store = InMemoryStore()

        # Required methods should exist
        assert hasattr(store, 'store')
        assert hasattr(store, 'search')
        assert hasattr(store, 'get')
        assert hasattr(store, 'get_all')

        # Methods should be callable
        assert callable(store.store)
        assert callable(store.search)
        assert callable(store.get)
        assert callable(store.get_all)

    def test_memory_facade_interface_compatibility(self):
        """Test that Memory facade interface remains compatible."""
        memory = Memory()

        # Required methods should exist
        assert hasattr(memory, 'store')
        assert hasattr(memory, 'search')
        assert hasattr(memory, 'get')
        assert hasattr(memory, 'get_all')

        # Methods should be callable
        assert callable(memory.store)
        assert callable(memory.search)
        assert callable(memory.get)
        assert callable(memory.get_all)

    def test_agent_context_interface_compatibility(self):
        """Test that AgentContext interface remains compatible."""
        context = create_agent_context()

        # Required attributes
        assert hasattr(context, 'session_id')
        assert hasattr(context, 'store_memory')
        assert hasattr(context, 'search_memories')
        assert hasattr(context, 'get_session_memories')

        # Methods should be callable
        assert callable(context.store_memory)
        assert callable(context.search_memories)
        assert callable(context.get_session_memories)

    def test_memory_search_result_structure(self):
        """Test that MemorySearchResult structure is stable."""
        store = InMemoryStore()
        store.store("key1", {"data": "test"}, ["tag1"])

        result = store.search(["tag1"])

        # Required fields
        assert hasattr(result, 'records')
        assert hasattr(result, 'total_count')
        assert hasattr(result, 'search_query')
        assert hasattr(result, 'execution_time_ms')

        # Verify types
        assert isinstance(result.records, list)
        assert isinstance(result.total_count, int)
        assert isinstance(result.search_query, dict)
        assert isinstance(result.execution_time_ms, (int, float))

    def test_memory_record_structure(self):
        """Test that MemoryRecord structure is stable."""
        store = InMemoryStore()
        store.store("key1", {"data": "test"}, ["tag1"])

        record = store.get("key1")

        # Required fields
        assert hasattr(record, 'key')
        assert hasattr(record, 'content')
        assert hasattr(record, 'tags')
        assert hasattr(record, 'timestamp')
        assert hasattr(record, 'priority')
        assert hasattr(record, 'metadata')

        # Verify types
        assert isinstance(record.key, str)
        assert isinstance(record.tags, list)
        from datetime import datetime
        assert isinstance(record.timestamp, datetime)

    def test_agent_creation_default_parameters_stable(self):
        """Test that default parameters for agent creation are stable."""
        with patch('agency_code_agent.agency_code_agent.Agent') as mock_agent, \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5-mini"

            # Create with defaults
            create_agency_code_agent()

            call_kwargs = mock_agent.call_args[1]

            # Required parameters should be present
            assert 'name' in call_kwargs
            assert 'description' in call_kwargs
            assert 'instructions' in call_kwargs
            assert 'tools' in call_kwargs
            assert 'tools_folder' in call_kwargs
            assert 'model' in call_kwargs

            # Name should be consistent
            assert call_kwargs['name'] == "AgencyCodeAgent"

    def test_model_policy_keys_stable(self):
        """Test that model policy keys remain stable."""
        # Expected keys should exist
        expected_keys = {
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
        }

        for key in expected_keys:
            # Should not raise KeyError
            model = agent_model(key)
            assert isinstance(model, str)
            assert len(model) > 0

    def test_model_policy_defaults_stable(self):
        """Test that DEFAULTS dictionary structure is stable."""
        from shared.model_policy import DEFAULTS

        # Should be a dict
        assert isinstance(DEFAULTS, dict)

        # Should have expected keys
        expected_keys = {
            "planner", "chief_architect", "coder", "auditor",
            "quality_enforcer", "merger", "learning",
            "test_generator", "summary", "toolsmith"
        }

        for key in expected_keys:
            assert key in DEFAULTS, f"Expected key '{key}' missing from DEFAULTS"


class TestDataStructureStability:
    """Test that data structures remain stable across versions."""

    def test_memory_to_dict_format(self):
        """Test that memory to_dict format is stable."""
        store = InMemoryStore()
        store.store("key1", {"data": "test"}, ["tag1"])

        record = store.get("key1")
        record_dict = record.to_dict()

        # Required fields in dict format
        assert 'key' in record_dict
        assert 'content' in record_dict
        assert 'tags' in record_dict
        assert 'timestamp' in record_dict
        assert 'priority' in record_dict

    def test_agent_context_memory_format(self):
        """Test that AgentContext memory format is stable."""
        context = create_agent_context()
        context.store_memory("key1", {"data": "test"}, ["tag1"])

        memories = context.search_memories(["tag1"])

        # Should return list of dicts
        assert isinstance(memories, list)
        if len(memories) > 0:
            memory = memories[0]
            assert isinstance(memory, dict)
            assert 'key' in memory
            assert 'content' in memory
            assert 'tags' in memory

    def test_enhanced_memory_search_result_format(self):
        """Test that EnhancedMemoryStore search result format is stable."""
        with patch('agency_memory.enhanced_memory_store.VectorStore'):
            store = EnhancedMemoryStore()
            store.store("key1", {"data": "test"}, ["tag1"])

            result = store.search(["tag1"])

            # Should have stable structure
            assert hasattr(result, 'records')
            assert hasattr(result, 'total_count')
            assert isinstance(result.records, list)


class TestConfigurationConsistency:
    """Test configuration consistency across sessions."""

    def test_session_id_format_consistency(self):
        """Test that session ID format is consistent."""
        # Create multiple contexts
        contexts = [create_agent_context() for _ in range(5)]

        for context in contexts:
            # All should have session_id attribute
            assert hasattr(context, 'session_id')
            session_id = context.session_id

            # Should be a string
            assert isinstance(session_id, str)

            # Should not be empty
            assert len(session_id) > 0

            # Should start with "session_"
            assert session_id.startswith("session_")

    def test_agent_name_consistency(self):
        """Test that agent name is consistent."""
        with patch('agency_code_agent.agency_code_agent.Agent') as mock_agent, \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5-mini"

            # Create multiple times
            for _ in range(3):
                create_agency_code_agent()

                call_kwargs = mock_agent.call_args[1]
                name = call_kwargs['name']

                # Name should always be the same
                assert name == "AgencyCodeAgent"

    def test_tools_folder_path_consistency(self):
        """Test that tools folder path is consistent."""
        with patch('agency_code_agent.agency_code_agent.Agent') as mock_agent, \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5-mini"

            create_agency_code_agent()

            call_kwargs = mock_agent.call_args[1]
            tools_folder = call_kwargs.get('tools_folder')

            # Should be a valid path
            assert isinstance(tools_folder, str)
            assert len(tools_folder) > 0


class TestVersionCompatibility:
    """Test version compatibility indicators."""

    def test_memory_api_version_marker(self):
        """Test that memory API has version compatibility markers."""
        from agency_memory import memory

        # Module should exist
        assert memory is not None

        # Key classes should exist
        assert hasattr(memory, 'Memory')
        assert hasattr(memory, 'MemoryStore')
        assert hasattr(memory, 'InMemoryStore')

    def test_agent_context_api_version_marker(self):
        """Test that agent_context API has version compatibility markers."""
        from shared import agent_context

        # Module should exist
        assert agent_context is not None

        # Key classes/functions should exist
        assert hasattr(agent_context, 'AgentContext')
        assert hasattr(agent_context, 'create_agent_context')

    def test_model_policy_api_version_marker(self):
        """Test that model_policy API has version compatibility markers."""
        from shared import model_policy

        # Module should exist
        assert model_policy is not None

        # Key functions should exist
        assert hasattr(model_policy, 'agent_model')
        assert hasattr(model_policy, 'DEFAULTS')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])