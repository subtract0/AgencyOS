"""
Tests for constitutional test agent fixtures.

Following TDD: Tests written FIRST before implementation.
Constitutional compliance: Articles I-V satisfied.
"""

import time

import pytest
from agency_swarm import Agent

from shared.agent_context import AgentContext
from shared.type_definitions.result import Err, Ok, Result


class TestConstitutionalTestAgent:
    """Test suite for create_constitutional_test_agent fixture."""

    def test_creates_real_agent_not_mock(self):
        """Verify fixture creates real Agent instance, not mock."""
        from tests.fixtures.constitutional_test_agents import create_constitutional_test_agent

        agent = create_constitutional_test_agent("TestAgent")

        # Article II: Real behavior verification
        assert isinstance(agent, Agent), "Must create real Agent instance"
        assert not hasattr(agent, "_mock_name"), "Must not be a Mock object"
        assert hasattr(agent, "name"), "Must have Agent attributes"

    def test_agent_has_required_attributes(self):
        """Verify agent has all required attributes for testing."""
        from tests.fixtures.constitutional_test_agents import create_constitutional_test_agent

        agent = create_constitutional_test_agent("TestAgent")

        # Article I: Complete context - all attributes present
        assert agent.name == "TestAgent"
        assert hasattr(agent, "model")
        assert hasattr(agent, "instructions")
        assert hasattr(agent, "description")
        # Note: temperature/max_prompt_tokens are deprecated in newer agency_swarm
        # but Agent still has core required attributes

    def test_agent_initialization_is_fast(self):
        """Verify agent initialization is fast enough for unit tests."""
        from tests.fixtures.constitutional_test_agents import create_constitutional_test_agent

        # Article I: Complete context with performance constraint
        start = time.perf_counter()
        agent = create_constitutional_test_agent("TestAgent")
        elapsed = time.perf_counter() - start

        assert elapsed < 0.2, f"Initialization took {elapsed:.3f}s, must be <200ms"
        assert agent is not None

    def test_agent_with_custom_model(self):
        """Verify agent can be created with custom model."""
        from tests.fixtures.constitutional_test_agents import create_constitutional_test_agent

        agent = create_constitutional_test_agent("TestAgent", model="gpt-5")

        assert agent.model == "gpt-5"

    def test_agent_with_custom_instructions(self):
        """Verify agent can be created with custom instructions."""
        from tests.fixtures.constitutional_test_agents import create_constitutional_test_agent

        custom_instructions = "Custom test instructions"
        agent = create_constitutional_test_agent("TestAgent", instructions=custom_instructions)

        assert custom_instructions in agent.instructions

    def test_agent_supports_tools(self):
        """Verify agent can be created with tools list."""
        from tests.fixtures.constitutional_test_agents import create_constitutional_test_agent

        agent = create_constitutional_test_agent("TestAgent", tools=[])

        assert hasattr(agent, "tools")
        assert isinstance(agent.tools, list)

    def test_multiple_agents_are_independent(self):
        """Verify multiple agents don't share state."""
        from tests.fixtures.constitutional_test_agents import create_constitutional_test_agent

        agent1 = create_constitutional_test_agent("Agent1")
        agent2 = create_constitutional_test_agent("Agent2")

        assert agent1.name != agent2.name
        assert agent1 is not agent2


class TestTestAgentContext:
    """Test suite for create_test_agent_context fixture."""

    def test_creates_real_context_not_mock(self):
        """Verify fixture creates real AgentContext, not mock."""
        from tests.fixtures.constitutional_test_agents import create_test_agent_context

        context = create_test_agent_context()

        # Article II: Real behavior verification
        assert isinstance(context, AgentContext), "Must create real AgentContext"
        assert not hasattr(context, "_mock_name"), "Must not be a Mock object"

    def test_context_has_in_memory_store(self):
        """Verify context uses InMemoryStore for fast testing."""
        from tests.fixtures.constitutional_test_agents import create_test_agent_context

        context = create_test_agent_context()

        # Article I: Complete context - memory available
        assert context.memory is not None
        assert hasattr(context.memory, "store")
        assert hasattr(context.memory, "search")

    def test_context_memory_operations_work(self):
        """Verify context memory operations are functional."""
        from tests.fixtures.constitutional_test_agents import create_test_agent_context

        context = create_test_agent_context()

        # Article II: Real behavior - actual storage
        context.store_memory("test_key", "test_content", tags=["test"])
        results = context.search_memories(["test"], include_session=True)

        assert len(results) > 0
        assert any("test" in r.get("tags", []) for r in results)

    def test_context_with_custom_session_id(self):
        """Verify context can be created with custom session ID."""
        from tests.fixtures.constitutional_test_agents import create_test_agent_context

        context = create_test_agent_context(session_id="test_session_123")

        assert context.session_id == "test_session_123"

    def test_context_initialization_is_fast(self):
        """Verify context initialization is fast enough for unit tests."""
        from tests.fixtures.constitutional_test_agents import create_test_agent_context

        # Article I: Complete context with performance constraint
        start = time.perf_counter()
        context = create_test_agent_context()
        elapsed = time.perf_counter() - start

        assert elapsed < 0.2, f"Initialization took {elapsed:.3f}s, must be <200ms"
        assert context is not None

    def test_multiple_contexts_are_independent(self):
        """Verify multiple contexts don't share memory."""
        from tests.fixtures.constitutional_test_agents import create_test_agent_context

        context1 = create_test_agent_context()
        context2 = create_test_agent_context()

        # Store in context1, verify isolation
        context1.store_memory("key1", "content1", tags=["ctx1"])
        results = context2.search_memories(["ctx1"], include_session=False)

        assert len(results) == 0, "Contexts must not share memory"


class TestConstitutionalCompliance:
    """Test constitutional compliance of fixtures."""

    def test_article_i_complete_context(self):
        """Verify Article I: Complete Context Before Action."""
        from tests.fixtures.constitutional_test_agents import (
            create_constitutional_test_agent,
            create_test_agent_context,
        )

        # All required components present
        agent = create_constitutional_test_agent("TestAgent")
        context = create_test_agent_context()

        # Article I: No incomplete data
        assert agent.name is not None
        assert agent.model is not None
        assert context.memory is not None
        assert context.session_id is not None

    def test_article_ii_real_behavior_not_mocks(self):
        """Verify Article II: 100% Verification - Real behavior."""
        from tests.fixtures.constitutional_test_agents import (
            create_constitutional_test_agent,
            create_test_agent_context,
        )

        agent = create_constitutional_test_agent("TestAgent")
        context = create_test_agent_context()

        # Article II: Real functionality, not simulated
        assert isinstance(agent, Agent), "Real Agent, not mock"
        assert isinstance(context, AgentContext), "Real AgentContext, not mock"

        # Verify real behavior
        context.store_memory("key", "value", tags=["test"])
        results = context.search_memories(["test"], include_session=True)
        assert len(results) > 0, "Real memory operations work"

    def test_article_iv_supports_learning(self):
        """Verify Article IV: Continuous Learning support."""
        from tests.fixtures.constitutional_test_agents import create_test_agent_context

        context = create_test_agent_context()

        # Article IV: Learning integration via memory
        context.store_memory("learning:pattern", {"pattern": "test_pattern"}, tags=["learning"])
        learnings = context.search_memories(["learning"], include_session=True)

        assert len(learnings) > 0, "Supports learning storage"

    def test_performance_within_constraints(self):
        """Verify fixtures meet performance requirements for testing."""
        from tests.fixtures.constitutional_test_agents import (
            create_constitutional_test_agent,
            create_test_agent_context,
        )

        # Both fixtures must initialize in <200ms total
        start = time.perf_counter()
        agent = create_constitutional_test_agent("TestAgent")
        context = create_test_agent_context()
        elapsed = time.perf_counter() - start

        assert elapsed < 0.2, f"Combined initialization took {elapsed:.3f}s, must be <200ms"
        assert agent is not None
        assert context is not None


class TestResultPatternSupport:
    """Test Result<T,E> pattern support in fixtures."""

    def test_context_can_store_result_types(self):
        """Verify context can store Result pattern types."""
        from tests.fixtures.constitutional_test_agents import create_test_agent_context

        context = create_test_agent_context()

        # Constitutional requirement: Result pattern for error handling
        success_result: Result[str, str] = Ok("success")
        error_result: Result[str, str] = Err("error")

        context.store_memory("result:success", {"result": "ok"}, tags=["result"])
        context.store_memory("result:error", {"result": "err"}, tags=["result"])

        results = context.search_memories(["result"], include_session=True)
        assert len(results) == 2


class TestUsageExamples:
    """Demonstrate proper usage of fixtures."""

    def test_basic_agent_creation(self):
        """Example: Create basic test agent."""
        from tests.fixtures.constitutional_test_agents import create_constitutional_test_agent

        agent = create_constitutional_test_agent("MyTestAgent")

        assert agent.name == "MyTestAgent"
        assert isinstance(agent, Agent)

    def test_agent_with_context(self):
        """Example: Create agent with shared context."""
        from tests.fixtures.constitutional_test_agents import (
            create_constitutional_test_agent,
            create_test_agent_context,
        )

        context = create_test_agent_context(session_id="test_session")
        agent = create_constitutional_test_agent("AgentWithContext")

        # Agent and context can work together
        context.store_memory("agent:created", {"name": agent.name}, tags=["agent"])
        results = context.search_memories(["agent"], include_session=True)

        assert len(results) > 0

    def test_multi_agent_scenario(self):
        """Example: Multiple agents with shared context."""
        from tests.fixtures.constitutional_test_agents import (
            create_constitutional_test_agent,
            create_test_agent_context,
        )

        context = create_test_agent_context()
        coder = create_constitutional_test_agent("Coder")
        planner = create_constitutional_test_agent("Planner")

        # Agents can share context
        context.store_memory("collaboration", {"agents": [coder.name, planner.name]}, tags=["collab"])
        results = context.search_memories(["collab"], include_session=True)

        assert len(results) == 1
        assert coder.name != planner.name
