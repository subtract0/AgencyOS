"""
Agent Registry for DSPy Migration

Central registry for managing both DSPy and legacy agents,
enabling gradual migration and A/B testing capabilities.
"""

import logging
from typing import Dict, Any, Optional, Type, Callable, List
from .type_definitions import AgentMetadata, PerformanceMetrics
from enum import Enum
import importlib
import os

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of agents available in the system."""
    CODE = "code"
    AUDITOR = "auditor"
    PLANNER = "planner"
    LEARNING = "learning"
    CHIEF_ARCHITECT = "chief_architect"
    MERGER = "merger"
    QUALITY_ENFORCER = "quality_enforcer"
    TOOLSMITH = "toolsmith"
    WORK_COMPLETION = "work_completion"
    TEST_GENERATOR = "test_generator"


class AgentRegistry:
    """
    Central registry for all agents in the Agency system.

    Manages both DSPy-based and legacy agents, providing a unified
    interface for agent creation and management.
    """

    def __init__(self):
        """Initialize the agent registry."""
        self._dspy_agents: Dict[str, Type] = {}
        self._legacy_agents: Dict[str, Callable] = {}
        self._agent_metadata: Dict[str, AgentMetadata] = {}
        self._initialized = False
        self._fallback_enabled = True

    def initialize(self) -> None:
        """
        Initialize the registry by discovering available agents.
        """
        if self._initialized:
            return

        logger.info("Initializing Agent Registry...")

        # Register DSPy agents
        self._register_dspy_agents()

        # Register legacy agents
        self._register_legacy_agents()

        self._initialized = True
        logger.info(f"Registry initialized with {len(self._dspy_agents)} DSPy agents and {len(self._legacy_agents)} legacy agents")

    def _register_dspy_agents(self) -> None:
        """Register all available DSPy agents."""
        try:
            # Import DSPy agents
            from dspy_agents.modules.code_agent import DSPyCodeAgent
            from dspy_agents.modules.auditor_agent import DSPyAuditorAgent
            from dspy_agents.modules.planner_agent import DSPyPlannerAgent
            from dspy_agents.modules.learning_agent import DSPyLearningAgent
            from dspy_agents.modules.toolsmith_agent import DSPyToolsmithAgent

            self._dspy_agents["code"] = DSPyCodeAgent
            self._agent_metadata["code"] = {
                "type": "dspy",
                "version": "0.1.0",
                "capabilities": ["implementation", "testing", "refactoring", "debugging"],
                "performance_score": 0.85,
            }

            self._dspy_agents["auditor"] = DSPyAuditorAgent
            self._agent_metadata["auditor"] = {
                "type": "dspy",
                "version": "0.1.0",
                "capabilities": ["quality_assurance", "necessary_analysis", "coverage_analysis", "compliance_checking"],
                "performance_score": 0.88,
            }

            self._dspy_agents["planner"] = DSPyPlannerAgent
            self._agent_metadata["planner"] = {
                "type": "dspy",
                "version": "0.1.0",
                "capabilities": ["strategic_planning", "spec_generation", "task_orchestration", "architecture_design"],
                "performance_score": 0.90,
            }

            self._dspy_agents["learning"] = DSPyLearningAgent
            self._agent_metadata["learning"] = {
                "type": "dspy",
                "version": "0.1.0",
                "capabilities": ["pattern_extraction", "knowledge_consolidation", "insight_generation", "cross_session_learning"],
                "performance_score": 0.92,
            }

            self._dspy_agents["toolsmith"] = DSPyToolsmithAgent
            self._agent_metadata["toolsmith"] = {
                "type": "dspy",
                "version": "0.1.0",
                "capabilities": ["tool_creation", "test_generation", "scaffolding", "artifact_handoff"],
                "performance_score": 0.87,
            }

        except ImportError as e:
            logger.warning(f"Could not import DSPy agents: {e}")

    def _register_legacy_agents(self) -> None:
        """Register legacy agent creation functions."""
        try:
            # Import legacy agent creators
            from agency_code_agent.agency_code_agent import create_agency_code_agent
            from auditor_agent import create_auditor_agent
            from planner_agent.planner_agent import create_planner_agent
            from learning_agent import create_learning_agent
            from chief_architect_agent import create_chief_architect_agent
            from merger_agent.merger_agent import create_merger_agent
            from test_generator_agent import create_test_generator_agent
            from work_completion_summary_agent import create_work_completion_summary_agent
            from toolsmith_agent import create_toolsmith_agent

            # Register legacy agents
            self._legacy_agents.update({
                "code": create_agency_code_agent,
                "auditor": create_auditor_agent,
                "planner": create_planner_agent,
                "learning": create_learning_agent,
                "chief_architect": create_chief_architect_agent,
                "merger": create_merger_agent,
                "test_generator": create_test_generator_agent,
                "work_completion": create_work_completion_summary_agent,
                "toolsmith": create_toolsmith_agent,
            })

            # Add metadata for legacy agents
            for agent_name in self._legacy_agents:
                if agent_name not in self._agent_metadata:
                    self._agent_metadata[agent_name] = {
                        "type": "legacy",
                        "version": "1.0.0",
                        "capabilities": [],
                        "performance_score": 0.75,
                    }

        except ImportError as e:
            logger.error(f"Could not import legacy agents: {e}")

    def get_agent(
        self,
        name: str,
        prefer_dspy: bool = True,
        legacy_fallback: bool = True,
        **kwargs
    ) -> Any:
        """
        Get an agent instance by name.

        Args:
            name: Name of the agent to retrieve
            prefer_dspy: Whether to prefer DSPy implementation if available
            legacy_fallback: Whether to fall back to legacy if DSPy unavailable
            **kwargs: Additional arguments for agent creation

        Returns:
            Agent instance

        Raises:
            ValueError: If agent not found and no fallback available
        """
        if not self._initialized:
            self.initialize()

        agent_name = name.lower()

        # Try DSPy first if preferred
        if prefer_dspy and agent_name in self._dspy_agents:
            try:
                logger.info(f"Creating DSPy agent: {agent_name}")
                return self._create_dspy_agent(agent_name, **kwargs)
            except Exception as e:
                logger.error(f"Failed to create DSPy agent {agent_name}: {e}")
                if not legacy_fallback:
                    raise

        # Fall back to legacy agent
        if agent_name in self._legacy_agents:
            logger.info(f"Creating legacy agent: {agent_name}")
            return self._create_legacy_agent(agent_name, **kwargs)

        # Agent not found
        available = list(set(list(self._dspy_agents.keys()) + list(self._legacy_agents.keys())))
        raise ValueError(f"Agent '{name}' not found. Available agents: {available}")

    def _create_dspy_agent(self, name: str, **kwargs) -> Any:
        """
        Create a DSPy agent instance.

        Args:
            name: Agent name
            **kwargs: Agent configuration

        Returns:
            DSPy agent instance
        """
        agent_class = self._dspy_agents[name]

        # Extract DSPy-specific parameters
        model = kwargs.pop("model", "gpt-4o-mini")
        reasoning_effort = kwargs.pop("reasoning_effort", "medium")
        enable_learning = kwargs.pop("enable_learning", True)

        # Create agent with configuration
        agent = agent_class(
            model=model,
            reasoning_effort=reasoning_effort,
            enable_learning=enable_learning
        )

        return agent

    def _create_legacy_agent(self, name: str, **kwargs) -> Any:
        """
        Create a legacy agent instance.

        Args:
            name: Agent name
            **kwargs: Agent configuration

        Returns:
            Legacy agent instance
        """
        creator_func = self._legacy_agents[name]

        # Legacy agents typically need an agent_context
        from shared.agent_context import create_agent_context

        if "agent_context" not in kwargs:
            kwargs["agent_context"] = create_agent_context()

        return creator_func(**kwargs)

    def list_agents(self, agent_type: Optional[str] = None) -> List[AgentMetadata]:
        """
        List available agents with their metadata.

        Args:
            agent_type: Filter by type ("dspy" or "legacy")

        Returns:
            List of agent information dictionaries
        """
        if not self._initialized:
            self.initialize()

        agents = []

        # Collect all agents
        all_agent_names = set(list(self._dspy_agents.keys()) + list(self._legacy_agents.keys()))

        for agent_name in all_agent_names:
            metadata = self._agent_metadata.get(agent_name, {})

            # Apply filter if specified
            if agent_type and metadata.get("type") != agent_type:
                continue

            agent_info = {
                "name": agent_name,
                "type": metadata.get("type", "unknown"),
                "version": metadata.get("version", "unknown"),
                "capabilities": metadata.get("capabilities", []),
                "performance_score": metadata.get("performance_score", 0.0),
                "has_dspy": agent_name in self._dspy_agents,
                "has_legacy": agent_name in self._legacy_agents,
            }
            agents.append(agent_info)

        return agents

    def get_agent_metadata(self, name: str) -> AgentMetadata:
        """
        Get metadata for a specific agent.

        Args:
            name: Agent name

        Returns:
            Agent metadata dictionary

        Raises:
            ValueError: If agent not found
        """
        if not self._initialized:
            self.initialize()

        agent_name = name.lower()

        if agent_name in self._agent_metadata:
            return self._agent_metadata[agent_name].copy()

        raise ValueError(f"No metadata found for agent: {name}")

    def update_agent_metadata(
        self,
        name: str,
        metadata: AgentMetadata,
        merge: bool = True
    ) -> None:
        """
        Update metadata for an agent.

        Args:
            name: Agent name
            metadata: New metadata
            merge: Whether to merge with existing metadata
        """
        agent_name = name.lower()

        if merge and agent_name in self._agent_metadata:
            self._agent_metadata[agent_name].update(metadata)
        else:
            self._agent_metadata[agent_name] = metadata

    def register_dspy_agent(
        self,
        name: str,
        agent_class: Type,
        metadata: Optional[AgentMetadata] = None
    ) -> None:
        """
        Register a new DSPy agent.

        Args:
            name: Agent name
            agent_class: DSPy agent class
            metadata: Optional metadata
        """
        agent_name = name.lower()
        self._dspy_agents[agent_name] = agent_class

        if metadata:
            self._agent_metadata[agent_name] = metadata
        else:
            self._agent_metadata[agent_name] = {
                "type": "dspy",
                "version": "unknown",
                "capabilities": [],
                "performance_score": 0.0,
            }

        logger.info(f"Registered DSPy agent: {agent_name}")

    def register_legacy_agent(
        self,
        name: str,
        creator_func: Callable,
        metadata: Optional[AgentMetadata] = None
    ) -> None:
        """
        Register a new legacy agent.

        Args:
            name: Agent name
            creator_func: Agent creation function
            metadata: Optional metadata
        """
        agent_name = name.lower()
        self._legacy_agents[agent_name] = creator_func

        if metadata:
            self._agent_metadata[agent_name] = metadata
        else:
            self._agent_metadata[agent_name] = {
                "type": "legacy",
                "version": "unknown",
                "capabilities": [],
                "performance_score": 0.0,
            }

        logger.info(f"Registered legacy agent: {agent_name}")

    def get_performance_metrics(self) -> PerformanceMetrics:
        """
        Get performance metrics for all agents.

        Returns:
            Dictionary of performance metrics
        """
        if not self._initialized:
            self.initialize()

        metrics = {
            "total_agents": len(self._agent_metadata),
            "dspy_agents": len(self._dspy_agents),
            "legacy_agents": len(self._legacy_agents),
            "agents": {}
        }

        for agent_name, metadata in self._agent_metadata.items():
            metrics["agents"][agent_name] = {
                "type": metadata.get("type"),
                "performance_score": metadata.get("performance_score", 0.0),
                "version": metadata.get("version"),
            }

        # Calculate average scores
        scores = [m.get("performance_score", 0.0) for m in self._agent_metadata.values()]
        if scores:
            metrics["average_performance"] = sum(scores) / len(scores)
        else:
            metrics["average_performance"] = 0.0

        return metrics


# Global registry instance
_global_registry: Optional[AgentRegistry] = None


def get_global_registry() -> AgentRegistry:
    """
    Get the global agent registry instance.

    Returns:
        Global AgentRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
        _global_registry.initialize()
    return _global_registry


def create_agent(name: str, **kwargs) -> Any:
    """
    Convenience function to create an agent using the global registry.

    Args:
        name: Agent name
        **kwargs: Agent configuration

    Returns:
        Agent instance
    """
    registry = get_global_registry()
    return registry.get_agent(name, **kwargs)


def list_available_agents() -> List[AgentMetadata]:
    """
    List all available agents in the system.

    Returns:
        List of agent information
    """
    registry = get_global_registry()
    return registry.list_agents()