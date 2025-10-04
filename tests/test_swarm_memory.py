# mypy: disable-error-code="misc,assignment,arg-type,attr-defined,index,return-value,union-attr,dict-item"
"""
Test suite for SwarmMemory functionality.

Tests multi-agent memory sharing, prioritization, pruning,
and cross-agent retrieval capabilities.
"""

from datetime import datetime, timedelta

import pytest

from agency_memory.swarm_memory import MemoryPriority, SwarmMemory, SwarmMemoryStore
from agency_memory.vector_store import (
    EnhancedSwarmMemoryStore,
    SimilarityResult,
    VectorStore,
)


class TestSwarmMemoryStore:
    """Test SwarmMemoryStore functionality."""

    def test_initialization(self):
        """Test SwarmMemoryStore initialization."""
        store = SwarmMemoryStore(max_memories_per_agent=100, pruning_threshold=0.8)

        assert store.max_memories_per_agent == 100
        assert store.pruning_threshold == 0.8
        assert len(store._memories) == 0
        assert len(store._agent_namespaces) == 0

    def test_agent_namespacing(self):
        """Test that memories are properly namespaced by agent."""
        store = SwarmMemoryStore()

        # Store memories for different agents
        store.store("task1", "Agent A task", ["work"], agent_id="agent_a")
        store.store("task1", "Agent B task", ["work"], agent_id="agent_b")

        # Check namespacing
        assert "agent_a:task1" in store._memories
        assert "agent_b:task1" in store._memories
        assert store._memories["agent_a:task1"]["content"] == "Agent A task"
        assert store._memories["agent_b:task1"]["content"] == "Agent B task"

    def test_memory_priorities(self):
        """Test memory priority system."""
        store = SwarmMemoryStore()

        # Store memories with different priorities
        store.store("critical", "Critical task", ["urgent"], priority=MemoryPriority.CRITICAL)
        store.store("normal", "Normal task", ["routine"], priority=MemoryPriority.NORMAL)
        store.store("low", "Low priority task", ["optional"], priority=MemoryPriority.LOW)

        # Search with minimum priority filter
        high_priority = store.search(
            ["urgent", "routine", "optional"], min_priority=MemoryPriority.HIGH
        )
        assert high_priority.total_count == 1
        assert high_priority.records[0].key == "critical"

    def test_shared_memory(self):
        """Test cross-agent memory sharing."""
        store = SwarmMemoryStore()

        # Store shared memory
        store.store(
            "shared_knowledge",
            "Important shared info",
            ["shared", "important"],
            agent_id="agent_a",
            is_shared=True,
        )

        # Store private memory
        store.store(
            "private_task",
            "Private info",
            ["private"],
            agent_id="agent_a",
            is_shared=False,
        )

        # Agent B should see shared memory
        agent_b_results = store.search(["shared"], agent_id="agent_b", include_shared=True)
        assert agent_b_results.total_count == 1
        assert agent_b_results.records[0].key == "shared_knowledge"

        # Agent B should not see private memory
        agent_b_private = store.search(["private"], agent_id="agent_b", include_shared=True)
        assert agent_b_private.total_count == 0

    def test_memory_access_tracking(self):
        """Test that memory access is tracked."""
        store = SwarmMemoryStore()
        store.store("test", "content", ["tag"], agent_id="agent_a")

        # Initial access count should be 0
        memory = store._memories["agent_a:test"]
        assert memory["access_count"] == 0

        # Search should increment access count
        store.search(["tag"], agent_id="agent_a")
        assert memory["access_count"] == 1

    def test_memory_pruning(self):
        """Test memory pruning functionality."""
        store = SwarmMemoryStore(max_memories_per_agent=5, pruning_threshold=0.8)

        # Add memories that exceed the threshold (80% of 5 = 4)
        # Make them all low priority so they can actually be pruned
        for i in range(6):
            priority = MemoryPriority.LOW
            store.store(
                f"task_{i}",
                f"Task {i}",
                ["work"],
                agent_id="agent_a",
                priority=priority,
            )

        # Manually age some memories to make them eligible for pruning
        from datetime import timedelta

        old_time = (datetime.now() - timedelta(hours=2)).isoformat()

        # Make first 3 memories older so they can be pruned
        for i in range(3):
            key = f"agent_a:task_{i}"
            if key in store._memories:
                store._memories[key]["last_accessed"] = old_time

        # Manually call pruning since auto-pruning may not have been triggered
        store.prune_memories("agent_a")

        # Should have triggered pruning
        agent_memories = store.get_all("agent_a")
        assert agent_memories.total_count < 6  # Some memories should be pruned

        # Should still have some memories but fewer than we added
        assert agent_memories.total_count >= 3  # At least some should remain

    def test_agent_summary(self):
        """Test agent memory summary generation."""
        store = SwarmMemoryStore()

        # Add various memories
        store.store(
            "task1",
            "Task 1",
            ["work"],
            agent_id="agent_a",
            priority=MemoryPriority.HIGH,
            is_shared=True,
        )
        store.store(
            "task2",
            "Task 2",
            ["work"],
            agent_id="agent_a",
            priority=MemoryPriority.NORMAL,
        )
        store.store(
            "task3",
            "Task 3",
            ["personal"],
            agent_id="agent_a",
            priority=MemoryPriority.LOW,
        )

        summary = store.get_agent_summary("agent_a")

        assert summary["agent_id"] == "agent_a"
        assert summary["total_memories"] == 3
        assert summary["shared_memories"] == 1
        assert summary["priority_distribution"]["high"] == 1
        assert summary["priority_distribution"]["normal"] == 1
        assert summary["priority_distribution"]["low"] == 1

    def test_swarm_overview(self):
        """Test swarm-wide memory overview."""
        store = SwarmMemoryStore()

        # Add memories for multiple agents
        store.store("task1", "Agent A task", ["work"], agent_id="agent_a", is_shared=True)
        store.store("task2", "Agent B task", ["work"], agent_id="agent_b")

        overview = store.get_swarm_overview()

        assert overview["total_agents"] == 2
        assert overview["total_memories"] == 2
        assert overview["shared_memories"] == 1
        assert overview["sharing_percentage"] == 50.0
        assert "agent_a" in overview["agent_summaries"]
        assert "agent_b" in overview["agent_summaries"]

    def test_memory_consolidation(self):
        """Test memory consolidation functionality."""
        store = SwarmMemoryStore()

        # Add many low-priority memories
        for i in range(60):
            priority = MemoryPriority.LOW if i < 50 else MemoryPriority.HIGH
            store.store(
                f"task_{i}",
                f"Task {i}",
                ["work"],
                agent_id="agent_a",
                priority=priority,
            )

        # Consolidate memories
        result = store.consolidate_agent_memories("agent_a", max_summary_memories=30)

        assert result["action"] == "consolidated"
        assert result["memories_kept"] <= 30
        assert result["memories_summarized"] > 0

        # Check that consolidation summary was created
        agent_memories = store.get_all("agent_a")
        summary_memories = [m for m in agent_memories.records if "summary" in m.tags]
        assert len(summary_memories) > 0


class TestSwarmMemory:
    """Test SwarmMemory interface."""

    def test_initialization(self):
        """Test SwarmMemory initialization."""
        memory = SwarmMemory(agent_id="test_agent")

        assert memory.agent_id == "test_agent"
        assert isinstance(memory._store, SwarmMemoryStore)

    def test_store_with_defaults(self):
        """Test storing memories with default agent ID."""
        memory = SwarmMemory(agent_id="test_agent")

        memory.store("task1", "Test task", ["work"], priority=MemoryPriority.HIGH)

        # Should use default agent ID
        stored_memory = memory._store._memories["test_agent:task1"]
        assert stored_memory["agent_id"] == "test_agent"
        assert stored_memory["priority"] == MemoryPriority.HIGH.value

    def test_search_with_sharing(self):
        """Test search including shared memories."""
        memory = SwarmMemory(agent_id="agent_a")

        # Store shared memory as different agent
        memory.store("shared", "Shared info", ["knowledge"], is_shared=True, agent_id="agent_b")

        # Store private memory
        memory.store("private", "Private info", ["knowledge"])

        # Search should include shared memory
        results = memory.search(["knowledge"], include_shared=True)
        assert len(results) == 2

        # Search without shared should only show private
        results = memory.search(["knowledge"], include_shared=False)
        assert len(results) == 1
        assert results[0]["key"] == "private"

    def test_memory_sharing(self):
        """Test sharing existing memories."""
        memory = SwarmMemory(agent_id="agent_a")

        memory.store("test", "Test content", ["test"])

        # Share the memory
        success = memory.share_memory("test")
        assert success

        # Should now be in shared knowledge
        shared_memories = memory.get_shared_memories()
        assert len(shared_memories) == 1
        assert shared_memories[0]["key"] == "test"

    def test_get_summary(self):
        """Test getting agent summary."""
        memory = SwarmMemory(agent_id="test_agent")

        memory.store("task1", "Task 1", ["work"])
        memory.store("task2", "Task 2", ["work"], priority=MemoryPriority.HIGH)

        summary = memory.get_summary()
        assert summary["agent_id"] == "test_agent"
        assert summary["total_memories"] == 2

    def test_swarm_overview(self):
        """Test getting swarm overview."""
        memory = SwarmMemory(agent_id="agent_a")

        memory.store("task1", "Task 1", ["work"], agent_id="agent_a")
        memory.store("task2", "Task 2", ["work"], agent_id="agent_b")

        overview = memory.get_swarm_overview()
        assert overview["total_agents"] == 2
        assert overview["total_memories"] == 2


class TestVectorStore:
    """Test VectorStore functionality."""

    def test_initialization(self):
        """Test VectorStore initialization."""
        store = VectorStore()

        assert store._embedding_provider is None
        assert store._embedding_function is None
        assert len(store._embeddings) == 0

    def test_add_memory(self):
        """Test adding memory to vector store."""
        store = VectorStore()

        memory = {
            "key": "test",
            "content": "This is test content",
            "tags": ["test", "content"],
        }

        store.add_memory("test_key", memory)

        assert "test_key" in store._memory_texts
        assert "test content" in store._memory_texts["test_key"].lower()

    def test_keyword_search(self):
        """Test keyword-based search."""
        store = VectorStore()

        memories = [
            {
                "key": "task1",
                "content": "Python programming task",
                "tags": ["python", "code"],
            },
            {
                "key": "task2",
                "content": "Data analysis work",
                "tags": ["data", "analysis"],
            },
            {
                "key": "task3",
                "content": "Python data processing",
                "tags": ["python", "data"],
            },
        ]

        for i, memory in enumerate(memories):
            store.add_memory(f"key_{i}", memory)

        # Search for Python-related memories
        results = store.keyword_search("python programming", memories, top_k=5)

        assert len(results) > 0
        assert all(isinstance(result, SimilarityResult) for result in results)
        assert results[0].search_type == "keyword"

    def test_get_stats(self):
        """Test vector store statistics."""
        store = VectorStore()

        memory = {"key": "test", "content": "test content", "tags": ["test"]}
        store.add_memory("test_key", memory)

        stats = store.get_stats()

        assert stats["total_memories"] == 1
        assert stats["memories_with_embeddings"] == 0  # No embedding provider
        assert stats["embedding_available"] is False

    def test_remove_memory(self):
        """Test removing memory from vector store."""
        store = VectorStore()

        memory = {"key": "test", "content": "test content", "tags": ["test"]}
        store.add_memory("test_key", memory)

        assert "test_key" in store._memory_texts

        store.remove_memory("test_key")

        assert "test_key" not in store._memory_texts
        assert "test_key" not in store._embeddings


class TestEnhancedSwarmMemoryStore:
    """Test EnhancedSwarmMemoryStore functionality."""

    def test_initialization(self):
        """Test enhanced store initialization."""
        swarm_store = SwarmMemoryStore()
        vector_store = VectorStore()
        enhanced_store = EnhancedSwarmMemoryStore(swarm_store, vector_store)

        assert enhanced_store.swarm_store is swarm_store
        assert enhanced_store.vector_store is vector_store

    def test_store_in_both_stores(self):
        """Test that memories are stored in both swarm and vector stores."""
        swarm_store = SwarmMemoryStore()
        vector_store = VectorStore()
        enhanced_store = EnhancedSwarmMemoryStore(swarm_store, vector_store)

        enhanced_store.store("test", "Test content", ["test"], agent_id="agent_a")

        # Should be in swarm store
        assert "agent_a:test" in swarm_store._memories

        # Should be in vector store
        assert "agent_a:test" in vector_store._memory_texts

    def test_combined_search(self):
        """Test combined tag and semantic search."""
        swarm_store = SwarmMemoryStore()
        vector_store = VectorStore()
        enhanced_store = EnhancedSwarmMemoryStore(swarm_store, vector_store)

        # Store some memories
        enhanced_store.store(
            "task1", "Python programming task", ["python", "code"], agent_id="agent_a"
        )
        enhanced_store.store(
            "task2", "Data analysis work", ["data", "analysis"], agent_id="agent_a"
        )

        # Test tag-only search
        tag_results = enhanced_store.combined_search(tags=["python"], agent_id="agent_a")
        assert len(tag_results) == 1
        assert tag_results[0]["key"] == "task1"

        # Test query-only search (falls back to keyword search)
        query_results = enhanced_store.combined_search(query="programming", agent_id="agent_a")
        assert len(query_results) > 0

    def test_delegation_to_swarm_store(self):
        """Test that unknown methods are delegated to swarm store."""
        swarm_store = SwarmMemoryStore()
        enhanced_store = EnhancedSwarmMemoryStore(swarm_store)

        # Test that we can call swarm store methods
        summary = enhanced_store.get_agent_summary("test_agent")
        assert summary["agent_id"] == "test_agent"


class TestMemoryPriority:
    """Test MemoryPriority enum."""

    def test_priority_values(self):
        """Test priority enum values."""
        assert MemoryPriority.LOW.value == 1
        assert MemoryPriority.NORMAL.value == 2
        assert MemoryPriority.HIGH.value == 3
        assert MemoryPriority.CRITICAL.value == 4

    def test_priority_comparison(self):
        """Test priority comparison."""
        assert MemoryPriority.HIGH > MemoryPriority.NORMAL
        assert MemoryPriority.CRITICAL > MemoryPriority.HIGH
        assert MemoryPriority.LOW < MemoryPriority.NORMAL


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    def test_multi_agent_collaboration(self):
        """Test multi-agent collaboration scenario."""
        # Create shared store for both agents
        shared_store = SwarmMemoryStore()

        # Create two agents with shared memory store
        agent_a = SwarmMemory(store=shared_store, agent_id="researcher")
        agent_b = SwarmMemory(store=shared_store, agent_id="developer")

        # Researcher shares findings
        agent_a.store(
            "research_findings",
            "Important research data",
            ["research", "data"],
            priority=MemoryPriority.HIGH,
            is_shared=True,
        )

        # Developer searches for research data
        research_data = agent_b.search(["research"], include_shared=True)
        assert len(research_data) == 1
        assert research_data[0]["agent_id"] == "researcher"

        # Developer creates implementation based on research
        agent_b.store(
            "implementation",
            "Code based on research",
            ["code", "implementation"],
            priority=MemoryPriority.HIGH,
        )

        # Check swarm overview
        overview = agent_a.get_swarm_overview()
        assert overview["total_agents"] == 2
        assert overview["shared_memories"] == 1

    def test_memory_lifecycle_management(self):
        """Test complete memory lifecycle including pruning and consolidation."""
        memory = SwarmMemory(agent_id="worker", max_memories=20)

        # Add many memories over time - mostly low priority for realistic pruning
        for i in range(25):
            priority = (
                MemoryPriority.HIGH if i < 3 else MemoryPriority.LOW
            )  # Only first 3 are high priority
            memory.store(f"task_{i}", f"Task {i} content", ["work"], priority=priority)

        # Manually age some low priority memories for pruning
        old_time = (datetime.now() - timedelta(hours=2)).isoformat()
        for i in range(3, 20):  # Age memories 3-19 (low priority ones)
            key = f"worker:task_{i}"
            if key in memory._store._memories:
                memory._store._memories[key]["last_accessed"] = old_time

        # Manually trigger pruning
        memory.prune_memories()

        # Should have been pruned
        agent_memories = memory.get_all()
        # With aggressive pruning and high priority preservation, should be less than original
        assert len(agent_memories) < 25

        # High priority memories should be preserved (first 3)
        # Note: get_all() returns dicts with string priority values
        high_priority_count = sum(
            1 for m in agent_memories if m.get("priority") in ["high", "critical"]
        )
        assert high_priority_count == 3  # Should preserve all high priority ones

        # Test manual consolidation
        consolidation_result = memory.consolidate_memories(max_individual_memories=10)

        if consolidation_result["action"] == "consolidated":
            assert consolidation_result["memories_kept"] <= 10

            # Should have created a summary
            memories_after = memory.get_all()
            summary_memories = [m for m in memories_after if "summary" in m.get("tags", [])]
            assert len(summary_memories) > 0

    def test_priority_based_search(self):
        """Test searching with different priority levels."""
        memory = SwarmMemory(agent_id="manager")

        # Store memories with different priorities
        memory.store(
            "urgent_bug",
            "Critical bug fix needed",
            ["bug", "urgent"],
            priority=MemoryPriority.CRITICAL,
        )
        memory.store(
            "feature_request",
            "New feature idea",
            ["feature", "idea"],
            priority=MemoryPriority.NORMAL,
        )
        memory.store(
            "code_cleanup",
            "Clean up old code",
            ["cleanup", "maintenance"],
            priority=MemoryPriority.LOW,
        )

        # Search for high priority items only
        urgent_items = memory.search(
            ["bug", "feature", "cleanup"], min_priority=MemoryPriority.HIGH
        )
        assert len(urgent_items) == 1
        assert urgent_items[0]["key"] == "urgent_bug"

        # Search for all items
        all_items = memory.search(["bug", "feature", "cleanup"], min_priority=MemoryPriority.LOW)
        assert len(all_items) == 3

    def test_cross_agent_knowledge_sharing(self):
        """Test knowledge sharing between specialized agents."""
        # Create shared store for all agents
        shared_store = SwarmMemoryStore()

        # Create specialized agents with shared store
        researcher = SwarmMemory(store=shared_store, agent_id="researcher")
        developer = SwarmMemory(store=shared_store, agent_id="developer")
        tester = SwarmMemory(store=shared_store, agent_id="tester")

        # Researcher shares methodology
        researcher.store(
            "methodology",
            "Testing methodology for new features",
            ["testing", "methodology"],
            is_shared=True,
            priority=MemoryPriority.HIGH,
        )

        # Developer shares code patterns
        developer.store(
            "patterns",
            "Useful code patterns for testing",
            ["code", "patterns", "testing"],
            is_shared=True,
            priority=MemoryPriority.HIGH,
        )

        # Tester can access knowledge from both
        testing_knowledge = tester.search(["testing"], include_shared=True)
        assert len(testing_knowledge) == 2

        # Verify sources
        sources = {mem["agent_id"] for mem in testing_knowledge}
        assert "researcher" in sources
        assert "developer" in sources

        # Tester adds own insights
        tester.store(
            "test_cases",
            "Comprehensive test cases",
            ["testing", "cases"],
            is_shared=True,
        )

        # Now all agents can benefit
        comprehensive_testing = researcher.search(["testing"], include_shared=True)
        assert len(comprehensive_testing) == 3


if __name__ == "__main__":
    pytest.main([__file__])
