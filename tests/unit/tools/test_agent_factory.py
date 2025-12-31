"""
Tests for Agent Factory (Phase 5).

Tests the agent spawning and lifecycle management including:
- Template registration
- Agent spawning
- Lifecycle management
- Hooks and cleanup
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))


class TestAgentState:
    """Tests for AgentState enum."""

    def test_all_states_defined(self):
        """Test that all expected states are defined."""
        from tools.agent_factory import AgentState

        expected = ["CREATED", "INITIALIZING", "READY", "RUNNING",
                    "PAUSED", "COMPLETED", "FAILED", "TERMINATED"]
        for state in expected:
            assert hasattr(AgentState, state)


class TestAgentCapability:
    """Tests for AgentCapability enum."""

    def test_all_capabilities_defined(self):
        """Test that all expected capabilities are defined."""
        from tools.agent_factory import AgentCapability

        expected = ["CODE_GENERATION", "CODE_REVIEW", "TEST_GENERATION",
                    "QUALITY_ENFORCEMENT", "DOCUMENTATION", "REFACTORING"]
        for cap in expected:
            assert hasattr(AgentCapability, cap)


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_config_creation(self):
        """Test creating an agent config."""
        from tools.agent_factory import AgentCapability, AgentConfig

        config = AgentConfig(
            name="test_agent",
            agent_type="coder",
            capabilities=[AgentCapability.CODE_GENERATION],
            priority=7,
        )

        assert config.name == "test_agent"
        assert config.agent_type == "coder"
        assert config.priority == 7

    def test_config_defaults(self):
        """Test config default values."""
        from tools.agent_factory import AgentCapability, AgentConfig

        config = AgentConfig(
            name="test",
            agent_type="coder",
            capabilities=[AgentCapability.CODE_GENERATION],
        )

        assert config.priority == 5
        assert config.max_retries == 3
        assert config.memory_enabled is True


class TestAgentTemplate:
    """Tests for AgentTemplate dataclass."""

    def test_template_creation(self):
        """Test creating an agent template."""
        from tools.agent_factory import AgentCapability, AgentTemplate

        template = AgentTemplate(
            name="custom",
            description="A custom agent",
            default_capabilities=[AgentCapability.CODE_GENERATION],
            required_tools=["read", "write"],
        )

        assert template.name == "custom"
        assert len(template.default_capabilities) == 1


class TestAgentInstance:
    """Tests for AgentInstance dataclass."""

    def test_instance_creation(self):
        """Test creating an agent instance."""
        from datetime import datetime

        from tools.agent_factory import (
            AgentCapability,
            AgentConfig,
            AgentInstance,
            AgentState,
        )

        config = AgentConfig(
            name="test",
            agent_type="coder",
            capabilities=[AgentCapability.CODE_GENERATION],
        )

        instance = AgentInstance(
            id="agent-001",
            config=config,
            state=AgentState.CREATED,
            created_at=datetime.now(),
        )

        assert instance.id == "agent-001"
        assert instance.state == AgentState.CREATED
        assert instance.task_count == 0


class TestSpawnRequest:
    """Tests for SpawnRequest dataclass."""

    def test_spawn_request_creation(self):
        """Test creating a spawn request."""
        from tools.agent_factory import SpawnRequest

        request = SpawnRequest(
            agent_type="coder",
            task="Write a function",
            priority=8,
        )

        assert request.agent_type == "coder"
        assert request.task == "Write a function"
        assert request.priority == 8


class TestAgentFactory:
    """Tests for AgentFactory class."""

    @pytest.fixture
    def factory(self):
        """Create a fresh factory instance."""
        from tools.agent_factory import AgentFactory

        return AgentFactory()

    def test_default_templates_registered(self, factory):
        """Test that default templates are registered."""
        templates = factory.list_templates()

        assert "coder" in templates
        assert "reviewer" in templates
        assert "tester" in templates
        assert "planner" in templates

    def test_register_custom_template(self, factory):
        """Test registering a custom template."""
        from tools.agent_factory import AgentCapability, AgentTemplate

        template = AgentTemplate(
            name="custom_agent",
            description="A custom agent type",
            default_capabilities=[AgentCapability.DEBUGGING],
            required_tools=["read"],
        )

        result = factory.register_template(template)

        assert result.is_ok()
        assert "custom_agent" in factory.list_templates()

    def test_register_template_requires_name(self, factory):
        """Test that template registration requires name."""
        from tools.agent_factory import AgentCapability, AgentTemplate

        template = AgentTemplate(
            name="",
            description="No name",
            default_capabilities=[AgentCapability.DEBUGGING],
            required_tools=[],
        )

        result = factory.register_template(template)

        assert result.is_err()
        assert "name" in result.unwrap_err().lower()

    def test_spawn_agent(self, factory):
        """Test spawning an agent."""
        from tools.agent_factory import SpawnRequest

        request = SpawnRequest(
            agent_type="coder",
            task="Write tests",
        )

        result = factory.spawn(request)

        assert result.is_ok()
        spawn_result = result.unwrap()
        assert spawn_result.agent_id.startswith("coder-")
        assert spawn_result.spawn_time_ms >= 0

    def test_spawn_unknown_type_fails(self, factory):
        """Test that spawning unknown type fails."""
        from tools.agent_factory import SpawnRequest

        request = SpawnRequest(
            agent_type="nonexistent",
            task="Something",
        )

        result = factory.spawn(request)

        assert result.is_err()
        assert "Unknown" in result.unwrap_err()

    def test_start_agent(self, factory):
        """Test starting an agent."""
        from tools.agent_factory import AgentState, SpawnRequest

        # Spawn first
        request = SpawnRequest(agent_type="coder", task="Test")
        spawn_result = factory.spawn(request).unwrap()
        agent_id = spawn_result.agent_id

        # Start
        result = factory.start(agent_id)

        assert result.is_ok()
        instance = factory.get_instance(agent_id)
        assert instance.state == AgentState.RUNNING

    def test_pause_resume_agent(self, factory):
        """Test pausing and resuming an agent."""
        from tools.agent_factory import AgentState, SpawnRequest

        # Spawn and start
        request = SpawnRequest(agent_type="coder", task="Test")
        spawn_result = factory.spawn(request).unwrap()
        agent_id = spawn_result.agent_id
        factory.start(agent_id)

        # Pause
        result = factory.pause(agent_id)
        assert result.is_ok()
        assert factory.get_instance(agent_id).state == AgentState.PAUSED

        # Resume
        result = factory.resume(agent_id)
        assert result.is_ok()
        assert factory.get_instance(agent_id).state == AgentState.RUNNING

    def test_complete_agent(self, factory):
        """Test completing an agent."""
        from tools.agent_factory import AgentState, SpawnRequest

        request = SpawnRequest(agent_type="coder", task="Test")
        spawn_result = factory.spawn(request).unwrap()
        agent_id = spawn_result.agent_id
        factory.start(agent_id)

        result = factory.complete(agent_id, {"output": "done"})

        assert result.is_ok()
        instance = factory.get_instance(agent_id)
        assert instance.state == AgentState.COMPLETED
        assert instance.output == {"output": "done"}

    def test_fail_agent(self, factory):
        """Test marking agent as failed."""
        from tools.agent_factory import AgentState, SpawnRequest

        request = SpawnRequest(agent_type="coder", task="Test")
        spawn_result = factory.spawn(request).unwrap()
        agent_id = spawn_result.agent_id
        factory.start(agent_id)

        result = factory.fail(agent_id, "Something went wrong")

        assert result.is_ok()
        instance = factory.get_instance(agent_id)
        assert instance.state == AgentState.FAILED
        assert instance.last_error == "Something went wrong"

    def test_terminate_agent(self, factory):
        """Test terminating an agent."""
        from tools.agent_factory import AgentState, SpawnRequest

        request = SpawnRequest(agent_type="coder", task="Test")
        spawn_result = factory.spawn(request).unwrap()
        agent_id = spawn_result.agent_id

        result = factory.terminate(agent_id)

        assert result.is_ok()
        assert factory.get_instance(agent_id).state == AgentState.TERMINATED

    def test_get_running_instances(self, factory):
        """Test getting running instances."""
        from tools.agent_factory import SpawnRequest

        # Spawn and start multiple
        for i in range(3):
            request = SpawnRequest(agent_type="coder", task=f"Task {i}")
            spawn_result = factory.spawn(request).unwrap()
            factory.start(spawn_result.agent_id)

        running = factory.get_running_instances()

        assert len(running) == 3

    def test_get_child_agents(self, factory):
        """Test getting child agents."""
        from tools.agent_factory import SpawnRequest

        # Spawn parent
        parent_request = SpawnRequest(agent_type="orchestrator", task="Parent")
        parent_result = factory.spawn(parent_request).unwrap()
        parent_id = parent_result.agent_id

        # Spawn children
        for i in range(2):
            child_request = SpawnRequest(
                agent_type="coder",
                task=f"Child {i}",
                parent_agent_id=parent_id,
            )
            factory.spawn(child_request)

        children = factory.get_child_agents(parent_id)

        assert len(children) == 2

    def test_spawn_hooks(self, factory):
        """Test spawn hooks are called."""
        from tools.agent_factory import SpawnRequest

        hook_calls = []

        def spawn_hook(instance):
            hook_calls.append(instance.id)

        factory.add_spawn_hook(spawn_hook)

        request = SpawnRequest(agent_type="coder", task="Test")
        result = factory.spawn(request)

        assert result.is_ok()
        assert len(hook_calls) == 1

    def test_completion_hooks(self, factory):
        """Test completion hooks are called."""
        from tools.agent_factory import SpawnRequest

        hook_calls = []

        def completion_hook(instance):
            hook_calls.append(instance.id)

        factory.add_completion_hook(completion_hook)

        request = SpawnRequest(agent_type="coder", task="Test")
        spawn_result = factory.spawn(request).unwrap()
        factory.start(spawn_result.agent_id)
        factory.complete(spawn_result.agent_id)

        assert len(hook_calls) == 1

    def test_cleanup_completed(self, factory):
        """Test cleanup of completed agents."""
        from tools.agent_factory import SpawnRequest

        # Spawn and complete agents
        for i in range(5):
            request = SpawnRequest(agent_type="coder", task=f"Task {i}")
            spawn_result = factory.spawn(request).unwrap()
            factory.start(spawn_result.agent_id)
            factory.complete(spawn_result.agent_id)

        # Cleanup with 0 age (remove all completed)
        removed = factory.cleanup_completed(max_age_seconds=0)

        assert removed == 5
        assert len(factory.get_all_instances()) == 0

    def test_get_stats(self, factory):
        """Test getting factory statistics."""
        from tools.agent_factory import SpawnRequest

        # Spawn some agents
        for i in range(3):
            request = SpawnRequest(agent_type="coder", task=f"Task {i}")
            factory.spawn(request)

        stats = factory.get_stats()

        assert stats["total_instances"] == 3
        assert stats["templates_registered"] >= 6  # Default templates


class TestGlobalFactory:
    """Tests for global factory instance."""

    def test_get_factory_returns_instance(self):
        """Test that get_factory returns a factory."""
        from tools.agent_factory import AgentFactory, get_factory

        factory = get_factory()

        assert isinstance(factory, AgentFactory)

    def test_get_factory_returns_same_instance(self):
        """Test that get_factory returns the same instance."""
        from tools.agent_factory import get_factory

        factory1 = get_factory()
        factory2 = get_factory()

        assert factory1 is factory2
