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

        # Convert tools if provided
        lean_tools = []
        if tools:
            for tool in tools:
                if isinstance(tool, Tool):
                    lean_tools.append(tool)
                # Add more tool conversion logic as needed

        # Create config
        config = AgentConfig(
            name=name,
            instructions=instructions,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=lean_tools,
        )

        # Initialize parent
        super().__init__(config)


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
