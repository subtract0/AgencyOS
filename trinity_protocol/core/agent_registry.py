"""
Trinity Agent Registry - Unified factory for all Agency agents with hybrid model support.

Provides instantiation of all 10 Agency agents with configurable backends:
- LOCAL: Ollama models (qwen2.5-coder series)
- CLOUD: OpenAI models (GPT-5)

Constitutional Compliance:
- Article I: Complete context (retry with escalation)
- Article II: 100% verification (quality gates enforced)
- Article IV: Learning integration (VectorStore enabled)
"""

import logging
from enum import Enum
from typing import Literal

from agencyos_agent import create_agencyos_agent
from auditor_agent import create_auditor_agent
from chief_architect_agent import create_chief_architect_agent
from learning_agent import create_learning_agent
from merger_agent import create_merger_agent
from planner_agent import create_planner_agent
from quality_enforcer_agent import create_quality_enforcer_agent
from shared.agent_context import AgentContext
from shared.cost_tracker import CostTracker
from test_generator_agent import create_test_generator_agent
from toolsmith_agent import create_toolsmith_agent
from work_completion_summary_agent import create_work_completion_summary_agent

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """Model execution tiers for hybrid local-cloud architecture."""

    LOCAL = "local"  # Ollama models (free, slower)
    LOCAL_PLUS = "local_plus"  # Ollama with higher temperature/context
    CLOUD = "cloud"  # OpenAI GPT-5 (paid, faster, more capable)


class AgentType(Enum):
    """All available Agency agent types."""

    CODER = "coder"
    PLANNER = "planner"
    AUDITOR = "auditor"
    TEST_GENERATOR = "test_generator"
    QUALITY_ENFORCER = "quality_enforcer"
    LEARNING = "learning"
    CHIEF_ARCHITECT = "chief_architect"
    MERGER = "merger"
    TOOLSMITH = "toolsmith"
    SUMMARY = "summary"


# Model selection per tier and agent type
MODEL_MAP = {
    ModelTier.LOCAL: {
        AgentType.CODER: "ollama/qwen2.5-coder:32b",
        AgentType.PLANNER: "ollama/qwen2.5-coder:14b",
        AgentType.AUDITOR: "ollama/qwen2.5-coder:14b",
        AgentType.TEST_GENERATOR: "ollama/qwen2.5-coder:32b",
        AgentType.QUALITY_ENFORCER: "ollama/qwen2.5-coder:14b",
        AgentType.LEARNING: "ollama/qwen2.5-coder:14b",
        AgentType.CHIEF_ARCHITECT: "ollama/qwen2.5-coder:14b",
        AgentType.MERGER: "ollama/qwen2.5-coder:14b",
        AgentType.TOOLSMITH: "ollama/qwen2.5-coder:32b",
        AgentType.SUMMARY: "ollama/qwen2.5-coder:1.5b",
    },
    ModelTier.LOCAL_PLUS: {
        # Same models, but with temperature=0.7 and larger context
        AgentType.CODER: "ollama/qwen2.5-coder:32b",
        AgentType.PLANNER: "ollama/qwen2.5-coder:14b",
        AgentType.AUDITOR: "ollama/qwen2.5-coder:14b",
        AgentType.TEST_GENERATOR: "ollama/qwen2.5-coder:32b",
        AgentType.QUALITY_ENFORCER: "ollama/qwen2.5-coder:14b",
        AgentType.LEARNING: "ollama/qwen2.5-coder:14b",
        AgentType.CHIEF_ARCHITECT: "ollama/qwen2.5-coder:14b",
        AgentType.MERGER: "ollama/qwen2.5-coder:14b",
        AgentType.TOOLSMITH: "ollama/qwen2.5-coder:32b",
        AgentType.SUMMARY: "ollama/qwen2.5-coder:1.5b",
    },
    ModelTier.CLOUD: {
        # All agents use GPT-5 for cloud tier
        AgentType.CODER: "gpt-5",
        AgentType.PLANNER: "gpt-5",
        AgentType.AUDITOR: "gpt-5",
        AgentType.TEST_GENERATOR: "gpt-5",
        AgentType.QUALITY_ENFORCER: "gpt-5",
        AgentType.LEARNING: "gpt-5",
        AgentType.CHIEF_ARCHITECT: "gpt-5",
        AgentType.MERGER: "gpt-5",
        AgentType.TOOLSMITH: "gpt-5",
        AgentType.SUMMARY: "gpt-5-mini",  # Summary can use mini even in cloud
    },
}

# Reasoning effort per tier
REASONING_EFFORT_MAP = {
    ModelTier.LOCAL: "medium",  # Balanced for local models
    ModelTier.LOCAL_PLUS: "high",  # More exploration for retries
    ModelTier.CLOUD: "high",  # Max effort for cloud (we're paying for it)
}


class AgentRegistry:
    """
    Unified registry for creating Agency agents with hybrid model support.

    Manages agent instantiation across LOCAL (Ollama) and CLOUD (GPT-5) tiers
    with automatic escalation support.
    """

    def __init__(
        self,
        agent_context: AgentContext | None = None,
        cost_tracker: CostTracker | None = None,
        default_tier: ModelTier = ModelTier.LOCAL,
    ):
        """
        Initialize agent registry.

        Args:
            agent_context: Shared context for memory and learning
            cost_tracker: Cost tracking instance
            default_tier: Default model tier (LOCAL, LOCAL_PLUS, or CLOUD)
        """
        self.agent_context = agent_context
        self.cost_tracker = cost_tracker
        self.default_tier = default_tier
        self._agent_cache: dict[tuple[AgentType, ModelTier], object] = {}

        logger.info(f"AgentRegistry initialized with default_tier={default_tier.value}")

    def create_agent(self, agent_type: AgentType, tier: ModelTier | None = None) -> object:
        """
        Create an agent with specified type and model tier.

        Args:
            agent_type: Type of agent to create
            tier: Model tier (LOCAL, LOCAL_PLUS, CLOUD). Uses default if None.

        Returns:
            Instantiated agent
        """
        tier = tier or self.default_tier
        cache_key = (agent_type, tier)

        # Return cached instance if available
        if cache_key in self._agent_cache:
            logger.debug(f"Using cached {agent_type.value} agent (tier={tier.value})")
            return self._agent_cache[cache_key]

        # Get model and reasoning effort for this tier
        model = MODEL_MAP[tier][agent_type]
        reasoning_effort = REASONING_EFFORT_MAP[tier]

        logger.info(
            f"Creating {agent_type.value} agent: model={model}, reasoning={reasoning_effort}"
        )

        # Create agent using appropriate factory
        agent = self._create_agent_by_type(agent_type, model, reasoning_effort)

        # Cache and return
        self._agent_cache[cache_key] = agent
        return agent

    def get_model_for_agent(self, agent_type: AgentType, tier: ModelTier | None = None) -> str:
        """
        Get model name for an agent type at specified tier.

        Args:
            agent_type: Type of agent
            tier: Model tier (uses default if None)

        Returns:
            Model name string (e.g., "ollama/qwen2.5-coder:14b")
        """
        tier = tier or self.default_tier
        return MODEL_MAP[tier][agent_type]

    def _create_agent_by_type(
        self, agent_type: AgentType, model: str, reasoning_effort: str
    ) -> object:
        """Internal factory method to create agent by type."""
        factories = {
            AgentType.CODER: create_agencyos_agent,
            AgentType.PLANNER: create_planner_agent,
            AgentType.AUDITOR: create_auditor_agent,
            AgentType.TEST_GENERATOR: create_test_generator_agent,
            AgentType.QUALITY_ENFORCER: create_quality_enforcer_agent,
            AgentType.LEARNING: create_learning_agent,
            AgentType.CHIEF_ARCHITECT: create_chief_architect_agent,
            AgentType.MERGER: create_merger_agent,
            AgentType.TOOLSMITH: create_toolsmith_agent,
            AgentType.SUMMARY: create_work_completion_summary_agent,
        }

        # Agents that support cost_tracker parameter
        cost_tracker_supported = {
            AgentType.CODER,
            AgentType.TEST_GENERATOR,
            AgentType.QUALITY_ENFORCER,
            AgentType.MERGER,
            AgentType.TOOLSMITH,
            AgentType.SUMMARY,
        }

        factory = factories[agent_type]

        # Base parameters all agents support
        kwargs = {
            "model": model,
            "reasoning_effort": reasoning_effort,
            "agent_context": self.agent_context,
        }

        # Add cost_tracker only for agents that support it
        if agent_type in cost_tracker_supported and self.cost_tracker is not None:
            kwargs["cost_tracker"] = self.cost_tracker

        return factory(**kwargs)

    def create_all_agents(self, tier: ModelTier | None = None) -> dict[AgentType, object]:
        """
        Create all 10 Agency agents with specified tier.

        Args:
            tier: Model tier for all agents. Uses default if None.

        Returns:
            Dictionary mapping AgentType to instantiated agent
        """
        tier = tier or self.default_tier
        logger.info(f"Creating all agents with tier={tier.value}")

        return {agent_type: self.create_agent(agent_type, tier) for agent_type in AgentType}

    def escalate_agent(self, agent_type: AgentType, current_tier: ModelTier) -> object:
        """
        Create agent at next escalation tier.

        Escalation path: LOCAL → LOCAL_PLUS → CLOUD

        Args:
            agent_type: Type of agent to escalate
            current_tier: Current tier being used

        Returns:
            Agent at escalated tier, or CLOUD if already at max
        """
        escalation_map = {
            ModelTier.LOCAL: ModelTier.LOCAL_PLUS,
            ModelTier.LOCAL_PLUS: ModelTier.CLOUD,
            ModelTier.CLOUD: ModelTier.CLOUD,  # Already at max
        }

        next_tier = escalation_map[current_tier]
        logger.info(f"Escalating {agent_type.value}: {current_tier.value} → {next_tier.value}")

        return self.create_agent(agent_type, next_tier)

    def clear_cache(self) -> None:
        """Clear agent cache (useful for testing or memory management)."""
        logger.info("Clearing agent cache")
        self._agent_cache.clear()

    def get_model_for_tier(self, agent_type: AgentType, tier: ModelTier) -> str:
        """Get model string for given agent and tier (useful for debugging)."""
        return MODEL_MAP[tier][agent_type]


# Convenience factory function
def create_agent_registry(
    agent_context: AgentContext | None = None,
    cost_tracker: CostTracker | None = None,
    default_tier: Literal["local", "local_plus", "cloud"] = "local",
) -> AgentRegistry:
    """
    Create an AgentRegistry instance.

    Args:
        agent_context: Shared context for memory and learning
        cost_tracker: Cost tracking instance
        default_tier: Default model tier ("local", "local_plus", or "cloud")

    Returns:
        Configured AgentRegistry
    """
    tier_map = {
        "local": ModelTier.LOCAL,
        "local_plus": ModelTier.LOCAL_PLUS,
        "cloud": ModelTier.CLOUD,
    }

    return AgentRegistry(
        agent_context=agent_context,
        cost_tracker=cost_tracker,
        default_tier=tier_map[default_tier],
    )
