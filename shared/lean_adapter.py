"""
Backward Compatibility Adapter

Provides drop-in replacement for agency_swarm classes to ease migration.

This allows existing code like:
    from agency_swarm import Agent
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
        agents: list[Agent],
        shared_instructions: str | None = None,
        **kwargs,
    ):
        """
        Initialize agency with single agent.

        Args:
            agents: List of agents (we only use the first one)
            shared_instructions: Shared instructions (prepended to agent instructions)
            **kwargs: Ignored
        """
        if not agents:
            raise ValueError("Agency requires at least one agent")

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
