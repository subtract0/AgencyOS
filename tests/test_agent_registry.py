"""
Tests for Agent Registry - ensuring 100% coverage and robust behavior.

Every test adds value by verifying critical functionality.
"""

import json
import os
import tempfile
import pytest
from datetime import datetime
from pathlib import Path

from meta_learning.agent_registry import (
    AgentRegistry, Agent, AgentInstance, AIQEvent, AgentStatus
)


class TestAgentRegistryCore:
    """Core functionality tests."""

    def setup_method(self):
        """Setup with temporary storage."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.registry = AgentRegistry(storage_path=self.temp_file.name)

    def teardown_method(self):
        """Cleanup temporary files."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_register_agent_basic(self):
        """Test basic agent registration."""
        agent_id = self.registry.register_agent("TestAgent", "1.0.0")

        assert agent_id in self.registry.agents
        agent = self.registry.agents[agent_id]
        assert agent.name == "TestAgent"
        assert agent.version == "1.0.0"
        assert agent.status == AgentStatus.ACTIVE
        assert isinstance(agent.created_at, datetime)

    def test_register_agent_defaults(self):
        """Test agent registration with defaults."""
        agent_id = self.registry.register_agent("MinimalAgent")

        agent = self.registry.agents[agent_id]
        assert agent.version == "1.0.0"
        assert agent.status == AgentStatus.ACTIVE

    def test_create_instance_valid(self):
        """Test creating valid agent instance."""
        agent_id = self.registry.register_agent("TestAgent")
        config = {"param1": "value1", "param2": 42}

        instance_id = self.registry.create_instance(agent_id, config)

        assert instance_id in self.registry.instances
        instance = self.registry.instances[instance_id]
        assert instance.agent_id == agent_id
        assert instance.config == config
        assert isinstance(instance.created_at, datetime)

    def test_create_instance_invalid_agent(self):
        """Test creating instance for non-existent agent."""
        with pytest.raises(ValueError, match="Agent .* not found"):
            self.registry.create_instance("invalid-agent-id")

    def test_create_instance_no_config(self):
        """Test creating instance with no config."""
        agent_id = self.registry.register_agent("TestAgent")

        instance_id = self.registry.create_instance(agent_id)

        instance = self.registry.instances[instance_id]
        assert instance.config == {}

    def test_record_aiq_valid(self):
        """Test recording valid AIQ measurement."""
        agent_id = self.registry.register_agent("TestAgent")
        instance_id = self.registry.create_instance(agent_id)
        metrics = {"accuracy": 0.95, "speed": 1.2}

        event_id = self.registry.record_aiq(instance_id, 87.5, metrics)

        assert len(self.registry.aiq_events) == 1
        event = next(e for e in self.registry.aiq_events if e.event_id == event_id)
        assert event.agent_instance_id == instance_id
        assert event.aiq_score == 87.5
        assert event.metrics == metrics
        assert isinstance(event.timestamp, datetime)

    def test_record_aiq_invalid_instance(self):
        """Test recording AIQ for non-existent instance."""
        with pytest.raises(ValueError, match="Instance .* not found"):
            self.registry.record_aiq("invalid-instance-id", 75.0)

    def test_record_aiq_no_metrics(self):
        """Test recording AIQ without metrics."""
        agent_id = self.registry.register_agent("TestAgent")
        instance_id = self.registry.create_instance(agent_id)

        event_id = self.registry.record_aiq(instance_id, 80.0)

        event = next(e for e in self.registry.aiq_events if e.event_id == event_id)
        assert event.metrics == {}


class TestAgentRegistryQueries:
    """Test query functionality."""

    def setup_method(self):
        """Setup with temporary storage and test data."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.registry = AgentRegistry(storage_path=self.temp_file.name)

        # Create test data
        self.agent1_id = self.registry.register_agent("Agent1", "1.0.0")
        self.agent2_id = self.registry.register_agent("Agent2", "2.0.0")

        self.instance1_id = self.registry.create_instance(self.agent1_id)
        self.instance2_id = self.registry.create_instance(self.agent2_id)

        # Record some AIQ events
        self.registry.record_aiq(self.instance1_id, 85.0)
        self.registry.record_aiq(self.instance1_id, 87.5)
        self.registry.record_aiq(self.instance2_id, 92.0)

    def teardown_method(self):
        """Cleanup."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_get_agent_aiq_history(self):
        """Test getting AIQ history for agent."""
        history = self.registry.get_agent_aiq_history(self.agent1_id)

        assert len(history) == 2
        # Should be sorted by timestamp descending (newest first)
        assert history[0].aiq_score == 87.5
        assert history[1].aiq_score == 85.0

    def test_get_agent_aiq_history_with_limit(self):
        """Test AIQ history with limit."""
        history = self.registry.get_agent_aiq_history(self.agent1_id, limit=1)

        assert len(history) == 1
        assert history[0].aiq_score == 87.5

    def test_get_agent_aiq_history_no_events(self):
        """Test AIQ history for agent with no events."""
        agent_id = self.registry.register_agent("EmptyAgent")

        history = self.registry.get_agent_aiq_history(agent_id)

        assert history == []

    def test_get_top_performers(self):
        """Test getting top performing agents."""
        performers = self.registry.get_top_performers()

        assert len(performers) == 2
        # Should be sorted by score descending
        assert performers[0] == ("Agent2", 92.0)
        assert performers[1] == ("Agent1", 87.5)

    def test_get_top_performers_with_limit(self):
        """Test top performers with limit."""
        performers = self.registry.get_top_performers(limit=1)

        assert len(performers) == 1
        assert performers[0] == ("Agent2", 92.0)

    def test_get_top_performers_empty(self):
        """Test top performers with no events."""
        registry = AgentRegistry(storage_path=":memory:")

        performers = registry.get_top_performers()

        assert performers == []


class TestAgentRegistryPersistence:
    """Test persistence functionality."""

    def setup_method(self):
        """Setup with temporary storage."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')

    def teardown_method(self):
        """Cleanup."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_persistence_save_load(self):
        """Test save and load cycle."""
        # Create registry and add data
        registry1 = AgentRegistry(storage_path=self.temp_file.name)
        agent_id = registry1.register_agent("TestAgent", "1.0.0")
        instance_id = registry1.create_instance(agent_id, {"key": "value"})
        registry1.record_aiq(instance_id, 88.5, {"metric": 0.9})

        # Create new registry with same storage
        registry2 = AgentRegistry(storage_path=self.temp_file.name)

        # Verify data was loaded
        assert len(registry2.agents) == 1
        assert len(registry2.instances) == 1
        assert len(registry2.aiq_events) == 1

        # Verify agent data
        agent = registry2.agents[agent_id]
        assert agent.name == "TestAgent"
        assert agent.version == "1.0.0"

        # Verify instance data
        instance = registry2.instances[instance_id]
        assert instance.config == {"key": "value"}

        # Verify AIQ event data
        event = registry2.aiq_events[0]
        assert event.aiq_score == 88.5
        assert event.metrics == {"metric": 0.9}

    def test_persistence_corrupted_file(self):
        """Test handling of corrupted storage file."""
        # Write invalid JSON
        with open(self.temp_file.name, 'w') as f:
            f.write("invalid json content")

        # Should handle gracefully
        registry = AgentRegistry(storage_path=self.temp_file.name)

        # Should start with empty state
        assert len(registry.agents) == 0
        assert len(registry.instances) == 0
        assert len(registry.aiq_events) == 0

    def test_persistence_missing_file(self):
        """Test handling of missing storage file."""
        os.unlink(self.temp_file.name)

        registry = AgentRegistry(storage_path=self.temp_file.name)

        # Should start with empty state
        assert len(registry.agents) == 0
        assert len(registry.instances) == 0
        assert len(registry.aiq_events) == 0

    def test_persistence_creates_directory(self):
        """Test that storage directory is created if missing."""
        nonexistent_path = "/tmp/agency_test_nonexistent/registry.json"

        registry = AgentRegistry(storage_path=nonexistent_path)
        registry.register_agent("TestAgent")

        # Directory should be created and file should exist
        assert os.path.exists(nonexistent_path)

        # Cleanup
        os.unlink(nonexistent_path)
        os.rmdir(os.path.dirname(nonexistent_path))


class TestAgentRegistryEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Setup."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.registry = AgentRegistry(storage_path=self.temp_file.name)

    def teardown_method(self):
        """Cleanup."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_agent_status_enum_values(self):
        """Test all agent status enum values work."""
        agent_id = self.registry.register_agent("TestAgent")
        agent = self.registry.agents[agent_id]

        # Test all enum values
        for status in AgentStatus:
            agent.status = status
            self.registry._save()

            # Reload and verify
            registry2 = AgentRegistry(storage_path=self.temp_file.name)
            loaded_agent = registry2.agents[agent_id]
            assert loaded_agent.status == status

    def test_datetime_serialization(self):
        """Test datetime objects serialize/deserialize correctly."""
        agent_id = self.registry.register_agent("TestAgent")
        instance_id = self.registry.create_instance(agent_id)
        self.registry.record_aiq(instance_id, 75.0)

        # Reload from file
        registry2 = AgentRegistry(storage_path=self.temp_file.name)

        # Verify datetime objects are preserved
        agent = registry2.agents[agent_id]
        instance = registry2.instances[instance_id]
        event = registry2.aiq_events[0]

        assert isinstance(agent.created_at, datetime)
        assert isinstance(instance.created_at, datetime)
        assert isinstance(event.timestamp, datetime)

    def test_large_data_handling(self):
        """Test handling of larger datasets."""
        agent_id = self.registry.register_agent("TestAgent")
        instance_id = self.registry.create_instance(agent_id)

        # Record many AIQ events
        for i in range(100):
            self.registry.record_aiq(instance_id, float(i))

        assert len(self.registry.aiq_events) == 100

        # Test history with limit
        history = self.registry.get_agent_aiq_history(agent_id, limit=10)
        assert len(history) == 10

        # Should be newest first
        assert history[0].aiq_score == 99.0
        assert history[9].aiq_score == 90.0


if __name__ == "__main__":
    # Skip nested pytest execution to prevent recursion
    import os
    if os.environ.get("AGENCY_NESTED_TEST") != "1":
        pytest.main([__file__, "-v"])