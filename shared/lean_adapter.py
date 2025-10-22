"""
Backward Compatibility Adapter

Provides drop-in replacement for agency_swarm classes to ease migration.

This allows existing code like:
    from shared.lean_adapter import Agent
To work with:
    from shared.lean_adapter import Agent

Gradually migrate code to use LeanAgent directly for better performance.

Version: 1.0.0
Created: 2025-10-09
"""

from typing import Any

from shared.lean_agent import AgentConfig, LeanAgent, Tool


class ToolWrapper:
    """Wrapper to add .name attribute to tool classes/instances for backward compatibility."""

    def __init__(self, tool_or_class):
        self._tool = tool_or_class
        # Add .name attribute - handle both classes and instances
        if hasattr(tool_or_class, '__name__'):
            # It's a class
            self.name = tool_or_class.__name__
        else:
            # It's an instance - use class name
            self.name = tool_or_class.__class__.__name__

    def __getattr__(self, item):
        """Delegate all other attributes to the wrapped tool."""
        return getattr(self._tool, item)

    def __repr__(self):
        return f"ToolWrapper({self.name})"


class Agent(LeanAgent):
    """
    Drop-in replacement for agency_swarm.Agent.

    Accepts agency-swarm style kwargs and converts to LeanAgent config.

    Example:
        >>> agent = Agent(
        ...     name="coder",
        ...     instructions="You are helpful",
        ...     model="gpt-4o"
        ... )
    """

    def __init__(
        self,
        name: str = "agent",
        instructions: str | None = None,
        instructions_file: str | None = None,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        tools: list[Any] | None = None,
        description: str | None = None,  # Agent description for compatibility
        **kwargs,
    ):
        """
        Initialize agent with agency-swarm compatible interface.

        Args:
            name: Agent name
            instructions: System instructions string
            instructions_file: Path to instructions file (if not using string)
            model: LLM model name
            temperature: Sampling temperature
            max_tokens: Max response tokens
            tools: List of tools
            **kwargs: Ignored (for compatibility)
        """
        # Load instructions from file if provided
        if instructions_file and not instructions:
            from pathlib import Path

            try:
                instructions = Path(instructions_file).read_text()
            except FileNotFoundError:
                # File doesn't exist, use default instructions
                instructions = None

        if not instructions:
            instructions = f"You are {name}, a helpful AI assistant."

        # Store tools separately for backward compatibility
        # (agency-swarm tools don't match LeanAgent Tool Pydantic model)
        # Wrap tools to add .name attribute
        self._tools = [ToolWrapper(tool) for tool in (tools if tools else [])]

        # Create config without tools (tools stored separately)
        config = AgentConfig(
            name=name,
            instructions=instructions,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=[],  # Empty for now, agency-swarm tools stored in self._tools
        )

        # Initialize parent
        super().__init__(config)

        # Store description for backward compatibility
        self._description = description or f"{name} agent"

    # Property accessors for backward compatibility with tests
    @property
    def name(self) -> str:
        """Agent name (backward compatibility property)."""
        return self.config.name

    @property
    def description(self) -> str:
        """Agent description (backward compatibility property)."""
        return self._description

    @property
    def model(self) -> str:
        """LLM model name (backward compatibility property)."""
        return self.config.model

    @property
    def instructions(self) -> str:
        """System instructions (backward compatibility property)."""
        return self.config.instructions

    @property
    def temperature(self) -> float:
        """Sampling temperature (backward compatibility property)."""
        return self.config.temperature

    @property
    def max_tokens(self) -> int:
        """Max response tokens (backward compatibility property)."""
        return self.config.max_tokens

    @property
    def tools(self) -> list[Any]:
        """List of tools (backward compatibility property)."""
        return self._tools

    @property
    def hooks(self) -> dict[str, Any]:
        """Agent hooks (backward compatibility property, returns empty dict for now)."""
        return {}

    @property
    def tools_folder(self) -> str | None:
        """Tools folder path (backward compatibility property, returns None for now)."""
        return None

    @property
    def model_settings(self) -> dict[str, Any]:
        """Model settings (backward compatibility property)."""
        return {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }


class Agency:
    """
    Minimal Agency class for single-agent use.

    agency_swarm.Agency is complex multi-agent orchestration.
    For autonomous_worker, we only need single-agent execution.

    This provides compatibility without the overhead.
    """

    def __init__(
        self,
        *agents: Agent,
        shared_instructions: str | None = None,
        **kwargs,
    ):
        """
        Initialize agency with single agent or list of agents.

        Supports multiple calling patterns for backward compatibility:
        - Agency(agent) - single agent
        - Agency(agent1, agent2, agent3) - multiple agents (we use first)
        - Agency([agent1, agent2]) - list of agents
        - Agency(agents=[agent1, agent2]) - keyword argument

        Args:
            *agents: Variable number of Agent objects, or single list[Agent]
            shared_instructions: Shared instructions (prepended to agent instructions)
            **kwargs: Additional arguments (ignored for backward compatibility)
        """
        # Handle different calling patterns
        if not agents:
            # Check if agents passed as keyword arg
            if "agents" in kwargs:
                agents_arg = kwargs.pop("agents")
                if isinstance(agents_arg, list):
                    agents = tuple(agents_arg)
                else:
                    agents = (agents_arg,)
            else:
                raise ValueError("Agency requires at least one agent")

        # If first argument is a list, extract agents from it
        if len(agents) == 1 and isinstance(agents[0], list):
            agents = tuple(agents[0])

        if not agents:
            raise ValueError("Agency requires at least one agent")

        # Validate all agents
        for idx, agent in enumerate(agents):
            if not isinstance(agent, Agent):
                raise TypeError(
                    f"Agent at position {idx} must be Agent, got {type(agent).__name__}"
                )

        # Use first agent (for lean_adapter compatibility)
        self.agent = agents[0]

        # Prepend shared instructions if provided
        if shared_instructions:
            from pathlib import Path

            # Load from file if it's a path
            if shared_instructions.startswith("./") or shared_instructions.startswith("/"):
                try:
                    shared_instructions = Path(shared_instructions).read_text()
                except FileNotFoundError:
                    pass  # Use as-is if file doesn't exist

            # Prepend to agent instructions
            original_instructions = self.agent.config.instructions
            self.agent.config.instructions = f"{shared_instructions}\n\n{original_instructions}"

    def get_completion(self, message: str, recipient_agent: Agent | None = None) -> str:
        """
        Get completion from agent.

        Args:
            message: User message
            recipient_agent: Target agent (ignored, we only have one)

        Returns:
            Agent response
        """
        return self.agent.run(message)
