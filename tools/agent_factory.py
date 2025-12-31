"""
Agent Factory - Dynamic agent spawning and lifecycle management.

Creates, configures, and manages autonomous agents including:
- Agent template definitions
- Dynamic agent instantiation
- Capability assignment
- Resource allocation
- Lifecycle management

Constitutional Compliance:
- Article III: Automated enforcement (agents enforce quality)
- Article IV: Learning (agents learn from outcomes)
- Article VI: TDD (agents follow test-first approach)
"""

import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.type_definitions.result import Err, Ok, Result


class AgentState(Enum):
    """Agent lifecycle states."""

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


class AgentCapability(Enum):
    """Standard agent capabilities."""

    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    TEST_GENERATION = "test_generation"
    QUALITY_ENFORCEMENT = "quality_enforcement"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    DEBUGGING = "debugging"
    PLANNING = "planning"
    LEARNING = "learning"
    ORCHESTRATION = "orchestration"


@dataclass
class AgentConfig:
    """Configuration for an agent instance."""

    name: str
    agent_type: str
    capabilities: list[AgentCapability]
    priority: int = 5  # 1-10, higher = more priority
    max_retries: int = 3
    timeout_seconds: int = 300
    memory_enabled: bool = True
    learning_enabled: bool = True
    model_name: Optional[str] = None
    custom_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTemplate:
    """Template for creating agents of a specific type."""

    name: str
    description: str
    default_capabilities: list[AgentCapability]
    required_tools: list[str]
    initialization_hook: Optional[str] = None
    completion_hook: Optional[str] = None
    constitutional_requirements: list[str] = field(default_factory=list)


@dataclass
class AgentInstance:
    """A running agent instance."""

    id: str
    config: AgentConfig
    state: AgentState
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    task_count: int = 0
    success_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    output: Optional[dict] = None


@dataclass
class SpawnRequest:
    """Request to spawn a new agent."""

    agent_type: str
    task: str
    context: dict[str, Any] = field(default_factory=dict)
    priority: int = 5
    parent_agent_id: Optional[str] = None
    capabilities_override: Optional[list[AgentCapability]] = None


@dataclass
class SpawnResult:
    """Result of spawning an agent."""

    agent_id: str
    instance: AgentInstance
    spawn_time_ms: float


class AgentFactory:
    """
    Factory for creating and managing agent instances.

    Provides a unified interface for:
    - Registering agent templates
    - Spawning agent instances
    - Managing agent lifecycle
    - Monitoring agent health
    """

    # Default agent templates
    DEFAULT_TEMPLATES: dict[str, AgentTemplate] = {
        "coder": AgentTemplate(
            name="coder",
            description="Primary development agent for implementing features",
            default_capabilities=[
                AgentCapability.CODE_GENERATION,
                AgentCapability.REFACTORING,
                AgentCapability.DEBUGGING,
            ],
            required_tools=["read", "write", "edit", "bash"],
            constitutional_requirements=["Article VI: TDD", "Article II: 100% tests"],
        ),
        "reviewer": AgentTemplate(
            name="reviewer",
            description="Code review and quality analysis agent",
            default_capabilities=[
                AgentCapability.CODE_REVIEW,
                AgentCapability.QUALITY_ENFORCEMENT,
            ],
            required_tools=["read", "grep", "glob"],
            constitutional_requirements=["Article III: Automated enforcement"],
        ),
        "tester": AgentTemplate(
            name="tester",
            description="Test generation and validation agent",
            default_capabilities=[
                AgentCapability.TEST_GENERATION,
                AgentCapability.QUALITY_ENFORCEMENT,
            ],
            required_tools=["read", "write", "bash"],
            constitutional_requirements=["Article VI: TDD", "Article I: Complete context"],
        ),
        "planner": AgentTemplate(
            name="planner",
            description="Strategic planning and task breakdown agent",
            default_capabilities=[
                AgentCapability.PLANNING,
                AgentCapability.DOCUMENTATION,
            ],
            required_tools=["read", "write", "glob"],
            constitutional_requirements=["Article V: Spec-driven"],
        ),
        "learner": AgentTemplate(
            name="learner",
            description="Pattern extraction and learning agent",
            default_capabilities=[
                AgentCapability.LEARNING,
            ],
            required_tools=["read", "grep"],
            constitutional_requirements=["Article IV: Continuous learning"],
        ),
        "orchestrator": AgentTemplate(
            name="orchestrator",
            description="Multi-agent coordination and task routing",
            default_capabilities=[
                AgentCapability.ORCHESTRATION,
                AgentCapability.PLANNING,
            ],
            required_tools=["read"],
            constitutional_requirements=["All articles"],
        ),
    }

    def __init__(self):
        """Initialize the agent factory."""
        self._templates: dict[str, AgentTemplate] = dict(self.DEFAULT_TEMPLATES)
        self._instances: dict[str, AgentInstance] = {}
        self._spawn_hooks: list[Callable[[AgentInstance], None]] = []
        self._completion_hooks: list[Callable[[AgentInstance], None]] = []

    def register_template(self, template: AgentTemplate) -> Result[bool, str]:
        """
        Register a new agent template.

        Args:
            template: Agent template to register

        Returns:
            Result indicating success
        """
        if not template.name:
            return Err("Template name is required")

        if not template.default_capabilities:
            return Err("Template must have at least one capability")

        self._templates[template.name] = template
        return Ok(True)

    def get_template(self, name: str) -> Optional[AgentTemplate]:
        """Get an agent template by name."""
        return self._templates.get(name)

    def list_templates(self) -> list[str]:
        """List all registered template names."""
        return list(self._templates.keys())

    def spawn(self, request: SpawnRequest) -> Result[SpawnResult, str]:
        """
        Spawn a new agent instance.

        Args:
            request: Spawn request with agent type and task

        Returns:
            Result containing SpawnResult with agent ID
        """
        start_time = datetime.now()

        # Validate template exists
        template = self._templates.get(request.agent_type)
        if template is None:
            return Err(f"Unknown agent type: {request.agent_type}")

        # Create agent ID
        agent_id = f"{request.agent_type}-{uuid.uuid4().hex[:8]}"

        # Determine capabilities
        capabilities = request.capabilities_override or template.default_capabilities

        # Create config
        config = AgentConfig(
            name=f"{template.name}_{agent_id[-8:]}",
            agent_type=request.agent_type,
            capabilities=capabilities,
            priority=request.priority,
            custom_params={
                "task": request.task,
                "context": request.context,
                "parent_id": request.parent_agent_id,
            },
        )

        # Create instance
        instance = AgentInstance(
            id=agent_id,
            config=config,
            state=AgentState.CREATED,
            created_at=datetime.now(),
        )

        # Store instance
        self._instances[agent_id] = instance

        # Run spawn hooks
        for hook in self._spawn_hooks:
            try:
                hook(instance)
            except Exception:
                pass  # Hooks should not fail spawn

        # Calculate spawn time
        spawn_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        return Ok(
            SpawnResult(
                agent_id=agent_id,
                instance=instance,
                spawn_time_ms=spawn_time_ms,
            )
        )

    def start(self, agent_id: str) -> Result[bool, str]:
        """
        Start an agent instance.

        Args:
            agent_id: Agent ID to start

        Returns:
            Result indicating success
        """
        instance = self._instances.get(agent_id)
        if instance is None:
            return Err(f"Agent not found: {agent_id}")

        if instance.state not in (AgentState.CREATED, AgentState.READY, AgentState.PAUSED):
            return Err(f"Cannot start agent in state: {instance.state.value}")

        instance.state = AgentState.RUNNING
        instance.started_at = datetime.now()

        return Ok(True)

    def pause(self, agent_id: str) -> Result[bool, str]:
        """Pause a running agent."""
        instance = self._instances.get(agent_id)
        if instance is None:
            return Err(f"Agent not found: {agent_id}")

        if instance.state != AgentState.RUNNING:
            return Err(f"Cannot pause agent in state: {instance.state.value}")

        instance.state = AgentState.PAUSED
        return Ok(True)

    def resume(self, agent_id: str) -> Result[bool, str]:
        """Resume a paused agent."""
        instance = self._instances.get(agent_id)
        if instance is None:
            return Err(f"Agent not found: {agent_id}")

        if instance.state != AgentState.PAUSED:
            return Err(f"Cannot resume agent in state: {instance.state.value}")

        instance.state = AgentState.RUNNING
        return Ok(True)

    def complete(self, agent_id: str, output: Optional[dict] = None) -> Result[bool, str]:
        """
        Mark an agent as completed.

        Args:
            agent_id: Agent ID
            output: Optional output data

        Returns:
            Result indicating success
        """
        instance = self._instances.get(agent_id)
        if instance is None:
            return Err(f"Agent not found: {agent_id}")

        instance.state = AgentState.COMPLETED
        instance.completed_at = datetime.now()
        instance.output = output
        instance.success_count += 1

        # Run completion hooks
        for hook in self._completion_hooks:
            try:
                hook(instance)
            except Exception:
                pass

        return Ok(True)

    def fail(self, agent_id: str, error: str) -> Result[bool, str]:
        """
        Mark an agent as failed.

        Args:
            agent_id: Agent ID
            error: Error message

        Returns:
            Result indicating success
        """
        instance = self._instances.get(agent_id)
        if instance is None:
            return Err(f"Agent not found: {agent_id}")

        instance.state = AgentState.FAILED
        instance.completed_at = datetime.now()
        instance.last_error = error
        instance.error_count += 1

        return Ok(True)

    def terminate(self, agent_id: str) -> Result[bool, str]:
        """Forcefully terminate an agent."""
        instance = self._instances.get(agent_id)
        if instance is None:
            return Err(f"Agent not found: {agent_id}")

        instance.state = AgentState.TERMINATED
        instance.completed_at = datetime.now()

        return Ok(True)

    def get_instance(self, agent_id: str) -> Optional[AgentInstance]:
        """Get an agent instance by ID."""
        return self._instances.get(agent_id)

    def get_all_instances(self) -> list[AgentInstance]:
        """Get all agent instances."""
        return list(self._instances.values())

    def get_running_instances(self) -> list[AgentInstance]:
        """Get all running agent instances."""
        return [i for i in self._instances.values() if i.state == AgentState.RUNNING]

    def get_child_agents(self, parent_id: str) -> list[AgentInstance]:
        """Get all child agents of a parent."""
        children = []
        for instance in self._instances.values():
            parent = instance.config.custom_params.get("parent_id")
            if parent == parent_id:
                children.append(instance)
        return children

    def add_spawn_hook(self, hook: Callable[[AgentInstance], None]) -> None:
        """Add a hook called when agents spawn."""
        self._spawn_hooks.append(hook)

    def add_completion_hook(self, hook: Callable[[AgentInstance], None]) -> None:
        """Add a hook called when agents complete."""
        self._completion_hooks.append(hook)

    def cleanup_completed(self, max_age_seconds: int = 3600) -> int:
        """
        Remove completed agents older than max age.

        Args:
            max_age_seconds: Max age in seconds

        Returns:
            Number of agents removed
        """
        removed = 0
        now = datetime.now()
        to_remove = []

        for agent_id, instance in self._instances.items():
            if instance.state in (AgentState.COMPLETED, AgentState.FAILED, AgentState.TERMINATED):
                if instance.completed_at:
                    age = (now - instance.completed_at).total_seconds()
                    if age >= max_age_seconds:
                        to_remove.append(agent_id)

        for agent_id in to_remove:
            del self._instances[agent_id]
            removed += 1

        return removed

    def get_stats(self) -> dict:
        """Get factory statistics."""
        states: dict[str, int] = {}
        types: dict[str, int] = {}
        total_tasks = 0
        total_success = 0
        total_errors = 0

        for instance in self._instances.values():
            # Count by state
            state = instance.state.value
            states[state] = states.get(state, 0) + 1

            # Count by type
            agent_type = instance.config.agent_type
            types[agent_type] = types.get(agent_type, 0) + 1

            # Aggregate counts
            total_tasks += instance.task_count
            total_success += instance.success_count
            total_errors += instance.error_count

        return {
            "total_instances": len(self._instances),
            "by_state": states,
            "by_type": types,
            "total_tasks": total_tasks,
            "total_success": total_success,
            "total_errors": total_errors,
            "templates_registered": len(self._templates),
        }


# Global factory instance
_factory: Optional[AgentFactory] = None


def get_factory() -> AgentFactory:
    """Get the global agent factory instance."""
    global _factory
    if _factory is None:
        _factory = AgentFactory()
    return _factory


def main():
    """Command-line interface for agent factory."""
    import argparse

    parser = argparse.ArgumentParser(description="Agent factory CLI")
    parser.add_argument("--spawn", help="Spawn agent of type")
    parser.add_argument("--task", help="Task for spawned agent")
    parser.add_argument("--list-templates", action="store_true", help="List templates")
    parser.add_argument("--stats", action="store_true", help="Show factory stats")
    args = parser.parse_args()

    factory = get_factory()

    if args.list_templates:
        print("\n📋 Registered Agent Templates")
        print("=" * 50)
        for name in factory.list_templates():
            template = factory.get_template(name)
            if template:
                print(f"\n{name}:")
                print(f"  Description: {template.description}")
                print(f"  Capabilities: {[c.value for c in template.default_capabilities]}")
                print(f"  Tools: {template.required_tools}")

    elif args.spawn:
        task = args.task or "Default task"
        request = SpawnRequest(agent_type=args.spawn, task=task)
        result = factory.spawn(request)

        if result.is_ok():
            spawn_result = result.unwrap()
            print(f"\n✅ Spawned agent: {spawn_result.agent_id}")
            print(f"   Spawn time: {spawn_result.spawn_time_ms:.2f}ms")
            print(f"   State: {spawn_result.instance.state.value}")
        else:
            print(f"\n❌ Failed to spawn: {result.unwrap_err()}")

    elif args.stats:
        stats = factory.get_stats()
        print("\n📊 Agent Factory Statistics")
        print("=" * 50)
        print(f"Total instances: {stats['total_instances']}")
        print(f"Templates: {stats['templates_registered']}")
        if stats['by_state']:
            print("\nBy state:")
            for state, count in stats['by_state'].items():
                print(f"  {state}: {count}")
        if stats['by_type']:
            print("\nBy type:")
            for agent_type, count in stats['by_type'].items():
                print(f"  {agent_type}: {count}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
