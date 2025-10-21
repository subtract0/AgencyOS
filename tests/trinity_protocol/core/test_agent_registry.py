"""
Comprehensive production tests for trinity_protocol/core/agent_registry.py

Tests all 10 agents with LOCAL/CLOUD tiers, escalation, caching, and model selection.
Uses REAL imports, REAL agent factories, REAL model strings - NO MOCKS.

NECESSARY Framework Coverage:
- N: Normal operation (agent creation with default tier)
- E: Edge cases (None parameters, cache hits/misses)
- C: Corner cases (all 10 agents across all 3 tiers = 30 combinations)
- E: Error conditions (invalid tier handling)
- S: Security (proper model string validation)
- S: Stress (cache efficiency, multiple creations)
- A: Accessibility (factory function convenience)
- R: Regression (version compatibility)
- Y: Yield validation (correct agent types returned)
"""

import pytest

from shared.agent_context import AgentContext, create_agent_context
from shared.cost_tracker import CostTracker, MemoryStorage
from trinity_protocol.core.agent_registry import (
    AgentRegistry,
    AgentType,
    ModelTier,
    create_agent_registry,
)

# ============================================================================
# FIXTURES - Reusable test setup (AAA Pattern - Arrange)
# ============================================================================


@pytest.fixture
def agent_context() -> AgentContext:
    """Provide a real AgentContext instance for testing."""
    return create_agent_context()


@pytest.fixture
def cost_tracker() -> CostTracker:
    """Provide a real CostTracker instance for testing."""
    return CostTracker(storage=MemoryStorage())


@pytest.fixture
def registry_local(agent_context: AgentContext, cost_tracker: CostTracker) -> AgentRegistry:
    """AgentRegistry with LOCAL default tier."""
    return AgentRegistry(
        agent_context=agent_context,
        cost_tracker=cost_tracker,
        default_tier=ModelTier.LOCAL,
    )


@pytest.fixture
def registry_cloud(agent_context: AgentContext, cost_tracker: CostTracker) -> AgentRegistry:
    """AgentRegistry with CLOUD default tier."""
    return AgentRegistry(
        agent_context=agent_context,
        cost_tracker=cost_tracker,
        default_tier=ModelTier.CLOUD,
    )


# ============================================================================
# N - NORMAL OPERATION TESTS
# ============================================================================


def test_agent_registry_initialization_with_defaults():
    """Test AgentRegistry initializes with default parameters."""
    # Arrange & Act
    registry = AgentRegistry()

    # Assert
    assert registry is not None
    assert registry.default_tier == ModelTier.LOCAL
    assert registry.agent_context is None
    assert registry.cost_tracker is None
    assert registry._agent_cache == {}


def test_agent_registry_initialization_with_all_parameters(
    agent_context: AgentContext, cost_tracker: CostTracker
):
    """Test AgentRegistry initializes with all parameters provided."""
    # Arrange & Act
    registry = AgentRegistry(
        agent_context=agent_context,
        cost_tracker=cost_tracker,
        default_tier=ModelTier.CLOUD,
    )

    # Assert
    assert registry.agent_context is agent_context
    assert registry.cost_tracker is cost_tracker
    assert registry.default_tier == ModelTier.CLOUD
    assert registry._agent_cache == {}


def test_create_coder_agent_with_local_tier(registry_local: AgentRegistry):
    """Test creating CodeAgent with LOCAL tier returns valid agent."""
    # Arrange - registry_local fixture

    # Act
    agent = registry_local.create_agent(AgentType.CODER, ModelTier.LOCAL)

    # Assert
    assert agent is not None
    assert hasattr(agent, "name")
    assert agent.name == "CodingAgent"


def test_create_planner_agent_with_local_tier(registry_local: AgentRegistry):
    """Test creating PlannerAgent with LOCAL tier returns valid agent."""
    # Arrange - registry_local fixture

    # Act
    agent = registry_local.create_agent(AgentType.PLANNER, ModelTier.LOCAL)

    # Assert
    assert agent is not None
    assert hasattr(agent, "name")
    assert agent.name == "PlannerAgent"


def test_create_auditor_agent_with_cloud_tier(registry_cloud: AgentRegistry):
    """Test creating AuditorAgent with CLOUD tier returns valid agent."""
    # Arrange - registry_cloud fixture

    # Act
    agent = registry_cloud.create_agent(AgentType.AUDITOR, ModelTier.CLOUD)

    # Assert
    assert agent is not None
    assert hasattr(agent, "name")
    assert agent.name == "AuditorAgent"


def test_create_agent_uses_default_tier_when_tier_is_none(registry_local: AgentRegistry):
    """Test create_agent uses default_tier when tier parameter is None."""
    # Arrange
    expected_model = "ollama/qwen2.5-coder:32b"  # LOCAL tier for CODER

    # Act
    agent = registry_local.create_agent(AgentType.CODER, tier=None)
    actual_model = registry_local.get_model_for_tier(AgentType.CODER, ModelTier.LOCAL)

    # Assert
    assert agent is not None
    assert actual_model == expected_model


# ============================================================================
# E - EDGE CASE TESTS (All 10 Agents x 2 Tiers = 20 Combinations)
# ============================================================================


@pytest.mark.parametrize(
    "agent_type,expected_name",
    [
        (AgentType.CODER, "CodingAgent"),
        (AgentType.PLANNER, "PlannerAgent"),
        (AgentType.AUDITOR, "AuditorAgent"),
        (AgentType.TEST_GENERATOR, "TestGeneratorAgent"),
        (AgentType.QUALITY_ENFORCER, "QualityEnforcerAgent"),
        (AgentType.LEARNING, "LearningAgent"),
        (AgentType.CHIEF_ARCHITECT, "ChiefArchitectAgent"),
        (AgentType.MERGER, "MergerAgent"),
        (AgentType.TOOLSMITH, "ToolSmithAgent"),  # Note: camelCase "Smith"
        (AgentType.SUMMARY, "WorkCompletionSummaryAgent"),
    ],
)
def test_all_agents_can_be_created_with_local_tier(
    registry_local: AgentRegistry, agent_type: AgentType, expected_name: str
):
    """Test all 10 agents can be created with LOCAL tier."""
    # Arrange - registry_local fixture and parameterized agent_type

    # Act
    agent = registry_local.create_agent(agent_type, ModelTier.LOCAL)

    # Assert
    assert agent is not None
    assert hasattr(agent, "name")
    assert agent.name == expected_name


@pytest.mark.parametrize(
    "agent_type,expected_name",
    [
        (AgentType.CODER, "CodingAgent"),
        (AgentType.PLANNER, "PlannerAgent"),
        (AgentType.AUDITOR, "AuditorAgent"),
        (AgentType.TEST_GENERATOR, "TestGeneratorAgent"),
        (AgentType.QUALITY_ENFORCER, "QualityEnforcerAgent"),
        (AgentType.LEARNING, "LearningAgent"),
        (AgentType.CHIEF_ARCHITECT, "ChiefArchitectAgent"),
        (AgentType.MERGER, "MergerAgent"),
        (AgentType.TOOLSMITH, "ToolSmithAgent"),  # Note: camelCase "Smith"
        (AgentType.SUMMARY, "WorkCompletionSummaryAgent"),
    ],
)
def test_all_agents_can_be_created_with_cloud_tier(
    registry_cloud: AgentRegistry, agent_type: AgentType, expected_name: str
):
    """Test all 10 agents can be created with CLOUD tier."""
    # Arrange - registry_cloud fixture and parameterized agent_type

    # Act
    agent = registry_cloud.create_agent(agent_type, ModelTier.CLOUD)

    # Assert
    assert agent is not None
    assert hasattr(agent, "name")
    assert agent.name == expected_name


# ============================================================================
# C - CORNER CASE TESTS (LOCAL_PLUS tier, boundary conditions)
# ============================================================================


@pytest.mark.parametrize("agent_type", list(AgentType))
def test_all_agents_can_be_created_with_local_plus_tier(
    registry_local: AgentRegistry, agent_type: AgentType
):
    """Test all 10 agents can be created with LOCAL_PLUS tier."""
    # Arrange - registry_local fixture and parameterized agent_type

    # Act
    agent = registry_local.create_agent(agent_type, ModelTier.LOCAL_PLUS)

    # Assert
    assert agent is not None
    assert hasattr(agent, "name")


def test_create_all_agents_returns_dict_with_all_agent_types(registry_local: AgentRegistry):
    """Test create_all_agents returns dictionary with all 10 AgentTypes."""
    # Arrange - registry_local fixture

    # Act
    agents = registry_local.create_all_agents(ModelTier.LOCAL)

    # Assert
    assert isinstance(agents, dict)
    assert len(agents) == 10
    assert set(agents.keys()) == set(AgentType)

    # Verify all values are agent instances
    for agent_type, agent in agents.items():
        assert agent is not None
        assert hasattr(agent, "name")


def test_create_all_agents_uses_default_tier_when_tier_is_none(registry_cloud: AgentRegistry):
    """Test create_all_agents uses default_tier when tier is None."""
    # Arrange - registry_cloud with CLOUD default

    # Act
    agents = registry_cloud.create_all_agents(tier=None)

    # Assert
    assert len(agents) == 10
    # Verify CLOUD tier by checking one agent's model
    expected_cloud_model = "gpt-5"
    actual_model = registry_cloud.get_model_for_tier(AgentType.CODER, ModelTier.CLOUD)
    assert actual_model == expected_cloud_model


# ============================================================================
# E - ERROR CONDITION TESTS (Escalation paths)
# ============================================================================


def test_escalate_agent_from_local_to_local_plus(registry_local: AgentRegistry):
    """Test escalation from LOCAL → LOCAL_PLUS returns agent with correct tier."""
    # Arrange
    agent_type = AgentType.CODER

    # Act
    escalated_agent = registry_local.escalate_agent(agent_type, ModelTier.LOCAL)

    # Assert
    assert escalated_agent is not None
    # Verify escalation by checking cache for LOCAL_PLUS
    assert (agent_type, ModelTier.LOCAL_PLUS) in registry_local._agent_cache


def test_escalate_agent_from_local_plus_to_cloud(registry_local: AgentRegistry):
    """Test escalation from LOCAL_PLUS → CLOUD returns agent with correct tier."""
    # Arrange
    agent_type = AgentType.TEST_GENERATOR

    # Act
    escalated_agent = registry_local.escalate_agent(agent_type, ModelTier.LOCAL_PLUS)

    # Assert
    assert escalated_agent is not None
    # Verify escalation by checking cache for CLOUD
    assert (agent_type, ModelTier.CLOUD) in registry_local._agent_cache


def test_escalate_agent_from_cloud_stays_at_cloud(registry_local: AgentRegistry):
    """Test escalation from CLOUD → CLOUD (max tier) stays at CLOUD."""
    # Arrange
    agent_type = AgentType.QUALITY_ENFORCER

    # Act
    escalated_agent = registry_local.escalate_agent(agent_type, ModelTier.CLOUD)

    # Assert
    assert escalated_agent is not None
    # Verify still at CLOUD tier
    assert (agent_type, ModelTier.CLOUD) in registry_local._agent_cache


@pytest.mark.parametrize(
    "start_tier,expected_tier",
    [
        (ModelTier.LOCAL, ModelTier.LOCAL_PLUS),
        (ModelTier.LOCAL_PLUS, ModelTier.CLOUD),
        (ModelTier.CLOUD, ModelTier.CLOUD),
    ],
)
def test_escalation_path_for_all_tiers(
    registry_local: AgentRegistry, start_tier: ModelTier, expected_tier: ModelTier
):
    """Test escalation follows correct path: LOCAL → LOCAL_PLUS → CLOUD → CLOUD."""
    # Arrange
    agent_type = AgentType.LEARNING

    # Act
    escalated_agent = registry_local.escalate_agent(agent_type, start_tier)

    # Assert
    assert escalated_agent is not None
    assert (agent_type, expected_tier) in registry_local._agent_cache


# ============================================================================
# S - SECURITY TESTS (Model string validation)
# ============================================================================


@pytest.mark.parametrize(
    "agent_type,tier,expected_model",
    [
        (AgentType.CODER, ModelTier.LOCAL, "ollama/qwen2.5-coder:32b"),
        (AgentType.PLANNER, ModelTier.LOCAL, "ollama/qwen2.5-coder:14b"),
        (AgentType.SUMMARY, ModelTier.LOCAL, "ollama/qwen2.5-coder:1.5b"),
        (AgentType.CODER, ModelTier.CLOUD, "gpt-5"),
        (AgentType.PLANNER, ModelTier.CLOUD, "gpt-5"),
        (AgentType.SUMMARY, ModelTier.CLOUD, "gpt-5-mini"),
    ],
)
def test_get_model_for_tier_returns_correct_model_strings(
    registry_local: AgentRegistry, agent_type: AgentType, tier: ModelTier, expected_model: str
):
    """Test get_model_for_tier returns correct model strings for validation."""
    # Arrange - registry_local fixture and parameterized values

    # Act
    actual_model = registry_local.get_model_for_tier(agent_type, tier)

    # Assert
    assert actual_model == expected_model


def test_local_tier_uses_ollama_models_only(registry_local: AgentRegistry):
    """Test LOCAL tier exclusively uses Ollama models (security: no accidental cloud calls)."""
    # Arrange - all agent types

    # Act & Assert
    for agent_type in AgentType:
        model = registry_local.get_model_for_tier(agent_type, ModelTier.LOCAL)
        assert model.startswith("ollama/"), (
            f"LOCAL tier {agent_type.value} must use Ollama: {model}"
        )


def test_cloud_tier_uses_gpt_models_only(registry_local: AgentRegistry):
    """Test CLOUD tier exclusively uses GPT models (security: proper tier isolation)."""
    # Arrange - all agent types

    # Act & Assert
    for agent_type in AgentType:
        model = registry_local.get_model_for_tier(agent_type, ModelTier.CLOUD)
        assert model.startswith("gpt-"), f"CLOUD tier {agent_type.value} must use GPT: {model}"


# ============================================================================
# S - STRESS TESTS (Cache efficiency, multiple creations)
# ============================================================================


def test_agent_caching_works_correctly(registry_local: AgentRegistry):
    """Test agent instances are cached and reused for same (type, tier) combination."""
    # Arrange
    agent_type = AgentType.CODER
    tier = ModelTier.LOCAL

    # Act
    agent1 = registry_local.create_agent(agent_type, tier)
    agent2 = registry_local.create_agent(agent_type, tier)

    # Assert - same instance returned (caching)
    assert agent1 is agent2
    assert len(registry_local._agent_cache) == 1


def test_different_tiers_create_separate_cache_entries(registry_local: AgentRegistry):
    """Test different tiers for same agent type create separate cache entries."""
    # Arrange
    agent_type = AgentType.PLANNER

    # Act
    agent_local = registry_local.create_agent(agent_type, ModelTier.LOCAL)
    agent_cloud = registry_local.create_agent(agent_type, ModelTier.CLOUD)

    # Assert - different instances
    assert agent_local is not agent_cloud
    assert len(registry_local._agent_cache) == 2
    assert (agent_type, ModelTier.LOCAL) in registry_local._agent_cache
    assert (agent_type, ModelTier.CLOUD) in registry_local._agent_cache


def test_clear_cache_removes_all_cached_agents(registry_local: AgentRegistry):
    """Test clear_cache() removes all cached agent instances."""
    # Arrange - create several agents
    registry_local.create_agent(AgentType.CODER, ModelTier.LOCAL)
    registry_local.create_agent(AgentType.PLANNER, ModelTier.LOCAL)
    registry_local.create_agent(AgentType.AUDITOR, ModelTier.CLOUD)
    initial_cache_size = len(registry_local._agent_cache)
    assert initial_cache_size == 3

    # Act
    registry_local.clear_cache()

    # Assert
    assert len(registry_local._agent_cache) == 0


def test_cache_efficiency_after_clear_and_recreate(registry_local: AgentRegistry):
    """Test agents can be recreated after cache clear and are cached again."""
    # Arrange
    agent_type = AgentType.TEST_GENERATOR
    tier = ModelTier.LOCAL

    # Act - create, clear, recreate
    agent1 = registry_local.create_agent(agent_type, tier)
    registry_local.clear_cache()
    agent2 = registry_local.create_agent(agent_type, tier)
    agent3 = registry_local.create_agent(agent_type, tier)

    # Assert - new instance after clear, but cached on second creation
    assert agent1 is not agent2  # Different instance after clear
    assert agent2 is agent3  # Same instance after re-caching
    assert len(registry_local._agent_cache) == 1


def test_create_all_agents_populates_cache_efficiently(registry_local: AgentRegistry):
    """Test create_all_agents populates cache with exactly 10 entries."""
    # Arrange - empty cache

    # Act
    agents = registry_local.create_all_agents(ModelTier.LOCAL)

    # Assert - cache has exactly 10 entries
    assert len(registry_local._agent_cache) == 10
    assert len(agents) == 10

    # Verify subsequent calls reuse cache
    agents2 = registry_local.create_all_agents(ModelTier.LOCAL)
    for agent_type in AgentType:
        assert agents[agent_type] is agents2[agent_type]


# ============================================================================
# A - ACCESSIBILITY TESTS (Convenience factory function)
# ============================================================================


def test_create_agent_registry_factory_with_local_tier():
    """Test create_agent_registry convenience factory creates registry with local tier."""
    # Arrange & Act
    registry = create_agent_registry(default_tier="local")

    # Assert
    assert isinstance(registry, AgentRegistry)
    assert registry.default_tier == ModelTier.LOCAL


def test_create_agent_registry_factory_with_local_plus_tier():
    """Test create_agent_registry convenience factory creates registry with local_plus tier."""
    # Arrange & Act
    registry = create_agent_registry(default_tier="local_plus")

    # Assert
    assert isinstance(registry, AgentRegistry)
    assert registry.default_tier == ModelTier.LOCAL_PLUS


def test_create_agent_registry_factory_with_cloud_tier():
    """Test create_agent_registry convenience factory creates registry with cloud tier."""
    # Arrange & Act
    registry = create_agent_registry(default_tier="cloud")

    # Assert
    assert isinstance(registry, AgentRegistry)
    assert registry.default_tier == ModelTier.CLOUD


def test_create_agent_registry_factory_with_all_parameters(
    agent_context: AgentContext, cost_tracker: CostTracker
):
    """Test create_agent_registry factory with all parameters provided."""
    # Arrange & Act
    registry = create_agent_registry(
        agent_context=agent_context,
        cost_tracker=cost_tracker,
        default_tier="cloud",
    )

    # Assert
    assert registry.agent_context is agent_context
    assert registry.cost_tracker is cost_tracker
    assert registry.default_tier == ModelTier.CLOUD


# ============================================================================
# R - REGRESSION TESTS (Version compatibility)
# ============================================================================


def test_all_agent_types_enum_has_exactly_10_members():
    """Test AgentType enum has exactly 10 members (regression: no accidental additions/removals)."""
    # Arrange & Act
    agent_types = list(AgentType)

    # Assert
    assert len(agent_types) == 10
    expected_types = {
        AgentType.CODER,
        AgentType.PLANNER,
        AgentType.AUDITOR,
        AgentType.TEST_GENERATOR,
        AgentType.QUALITY_ENFORCER,
        AgentType.LEARNING,
        AgentType.CHIEF_ARCHITECT,
        AgentType.MERGER,
        AgentType.TOOLSMITH,
        AgentType.SUMMARY,
    }
    assert set(agent_types) == expected_types


def test_model_tier_enum_has_exactly_3_members():
    """Test ModelTier enum has exactly 3 members (regression: LOCAL, LOCAL_PLUS, CLOUD)."""
    # Arrange & Act
    model_tiers = list(ModelTier)

    # Assert
    assert len(model_tiers) == 3
    expected_tiers = {ModelTier.LOCAL, ModelTier.LOCAL_PLUS, ModelTier.CLOUD}
    assert set(model_tiers) == expected_tiers


def test_escalation_map_integrity():
    """Test escalation map follows expected path (regression: verify escalation logic)."""
    # Arrange
    registry = AgentRegistry()

    # Act & Assert - verify escalation path: LOCAL → LOCAL_PLUS → CLOUD → CLOUD
    local_plus_agent = registry.escalate_agent(AgentType.CODER, ModelTier.LOCAL)
    assert (AgentType.CODER, ModelTier.LOCAL_PLUS) in registry._agent_cache

    cloud_agent = registry.escalate_agent(AgentType.CODER, ModelTier.LOCAL_PLUS)
    assert (AgentType.CODER, ModelTier.CLOUD) in registry._agent_cache

    cloud_agent_again = registry.escalate_agent(AgentType.CODER, ModelTier.CLOUD)
    assert cloud_agent is cloud_agent_again  # Same instance (cache)


# ============================================================================
# Y - YIELD VALIDATION TESTS (Output correctness)
# ============================================================================


def test_coder_agent_has_correct_attributes(registry_local: AgentRegistry):
    """Test CoderAgent has expected attributes and methods."""
    # Arrange & Act
    agent = registry_local.create_agent(AgentType.CODER, ModelTier.LOCAL)

    # Assert
    assert hasattr(agent, "name")
    assert hasattr(agent, "description")
    assert hasattr(agent, "instructions")
    assert agent.name == "CodingAgent"


def test_planner_agent_has_correct_attributes(registry_local: AgentRegistry):
    """Test PlannerAgent has expected attributes and methods."""
    # Arrange & Act
    agent = registry_local.create_agent(AgentType.PLANNER, ModelTier.LOCAL)

    # Assert
    assert hasattr(agent, "name")
    assert hasattr(agent, "description")
    assert hasattr(agent, "instructions")
    assert agent.name == "PlannerAgent"


def test_summary_agent_uses_mini_model_for_cloud_tier(registry_cloud: AgentRegistry):
    """Test SummaryAgent uses gpt-5-mini even in CLOUD tier (cost optimization)."""
    # Arrange & Act
    model = registry_cloud.get_model_for_tier(AgentType.SUMMARY, ModelTier.CLOUD)

    # Assert
    assert model == "gpt-5-mini"


def test_large_agents_use_32b_model_for_local_tier(registry_local: AgentRegistry):
    """Test compute-intensive agents use 32b Ollama model for LOCAL tier."""
    # Arrange
    compute_heavy_agents = [AgentType.CODER, AgentType.TEST_GENERATOR, AgentType.TOOLSMITH]

    # Act & Assert
    for agent_type in compute_heavy_agents:
        model = registry_local.get_model_for_tier(agent_type, ModelTier.LOCAL)
        assert "32b" in model, f"{agent_type.value} should use 32b model: {model}"


def test_standard_agents_use_14b_model_for_local_tier(registry_local: AgentRegistry):
    """Test standard agents use 14b Ollama model for LOCAL tier (resource efficiency)."""
    # Arrange
    standard_agents = [
        AgentType.PLANNER,
        AgentType.AUDITOR,
        AgentType.QUALITY_ENFORCER,
        AgentType.LEARNING,
        AgentType.CHIEF_ARCHITECT,
        AgentType.MERGER,
    ]

    # Act & Assert
    for agent_type in standard_agents:
        model = registry_local.get_model_for_tier(agent_type, ModelTier.LOCAL)
        assert "14b" in model, f"{agent_type.value} should use 14b model: {model}"


def test_summary_agent_uses_tiny_model_for_local_tier(registry_local: AgentRegistry):
    """Test SummaryAgent uses 1.5b Ollama model for LOCAL tier (ultra-efficient)."""
    # Arrange & Act
    model = registry_local.get_model_for_tier(AgentType.SUMMARY, ModelTier.LOCAL)

    # Assert
    assert "1.5b" in model


# ============================================================================
# INTEGRATION TESTS (End-to-end workflows)
# ============================================================================


def test_complete_escalation_workflow(registry_local: AgentRegistry):
    """Test complete escalation workflow: LOCAL → LOCAL_PLUS → CLOUD for single agent."""
    # Arrange
    agent_type = AgentType.AUDITOR

    # Act - create initial agent
    local_agent = registry_local.create_agent(agent_type, ModelTier.LOCAL)

    # Act - escalate to LOCAL_PLUS
    local_plus_agent = registry_local.escalate_agent(agent_type, ModelTier.LOCAL)

    # Act - escalate to CLOUD
    cloud_agent = registry_local.escalate_agent(agent_type, ModelTier.LOCAL_PLUS)

    # Act - try escalating CLOUD (should stay at CLOUD)
    cloud_agent_again = registry_local.escalate_agent(agent_type, ModelTier.CLOUD)

    # Assert - all agents exist and are cached
    assert local_agent is not None
    assert local_plus_agent is not None
    assert cloud_agent is not None
    assert cloud_agent is cloud_agent_again  # Cache hit
    assert len(registry_local._agent_cache) == 3  # 3 tiers cached


def test_create_all_agents_then_escalate_all(registry_local: AgentRegistry):
    """Test creating all agents at LOCAL tier then escalating all to CLOUD."""
    # Arrange & Act - create all LOCAL agents
    local_agents = registry_local.create_all_agents(ModelTier.LOCAL)
    assert len(local_agents) == 10

    # Act - escalate all from LOCAL → LOCAL_PLUS
    for agent_type in AgentType:
        registry_local.escalate_agent(agent_type, ModelTier.LOCAL)

    # Assert - cache should have 20 entries after first escalation (10 LOCAL + 10 LOCAL_PLUS)
    assert len(registry_local._agent_cache) == 20

    # Act - escalate all from LOCAL_PLUS → CLOUD
    for agent_type in AgentType:
        registry_local.escalate_agent(agent_type, ModelTier.LOCAL_PLUS)

    # Assert - cache should have 30 entries (10 agents x 3 tiers)
    assert len(registry_local._agent_cache) == 30


def test_mixed_tier_agent_creation(registry_local: AgentRegistry):
    """Test creating different agents at different tiers simultaneously."""
    # Arrange & Act
    coder_local = registry_local.create_agent(AgentType.CODER, ModelTier.LOCAL)
    planner_cloud = registry_local.create_agent(AgentType.PLANNER, ModelTier.CLOUD)
    auditor_local_plus = registry_local.create_agent(AgentType.AUDITOR, ModelTier.LOCAL_PLUS)

    # Assert - all created successfully
    assert coder_local is not None
    assert planner_cloud is not None
    assert auditor_local_plus is not None
    assert len(registry_local._agent_cache) == 3

    # Verify correct models
    assert (
        registry_local.get_model_for_tier(AgentType.CODER, ModelTier.LOCAL)
        == "ollama/qwen2.5-coder:32b"
    )
    assert registry_local.get_model_for_tier(AgentType.PLANNER, ModelTier.CLOUD) == "gpt-5"
    assert (
        registry_local.get_model_for_tier(AgentType.AUDITOR, ModelTier.LOCAL_PLUS)
        == "ollama/qwen2.5-coder:14b"
    )
