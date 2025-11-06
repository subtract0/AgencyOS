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

from pydantic import Field

from shared.lean_agent import AgentConfig, LeanAgent, Tool, ToolParameter


class BaseTool(Tool):
    """
    Backward-compatible Tool subclass that auto-fills required Pydantic fields.

    Legacy test pattern: tool = Bash(command="...")

    This class auto-fills missing metadata:
    - name: Defaults to class name
    - description: Defaults to first line of docstring
    - parameters: Defaults to permissive schema

    Explicit overrides are preserved.
    """

    # Internal execution context injected by runtime (excluded from schema)
    context_data: Any = Field(default=None, exclude=True, alias="_tool_exec_context")

    def __init__(self, **kwargs):
        """Initialize BaseTool with auto-filled metadata for backward compatibility."""
        # Normalize legacy context aliases before validation
        context_value = None
        if "context" in kwargs:
            context_value = kwargs.pop("context")
        elif "_tool_exec_context" in kwargs:
            context_value = kwargs.pop("_tool_exec_context")

        # Auto-fill 'name' if not provided
        if "name" not in kwargs:
            kwargs["name"] = self.__class__.__name__

        # Auto-fill 'description' if not provided
        if "description" not in kwargs:
            # Extract first non-empty line from docstring
            docstring = self.__class__.__doc__
            if docstring:
                lines = docstring.strip().split('\n')
                first_line = next((line.strip() for line in lines if line.strip()), None)
                kwargs["description"] = first_line if first_line else f"{self.__class__.__name__} tool"
            else:
                kwargs["description"] = f"{self.__class__.__name__} tool"

        # Auto-fill 'parameters' if not provided (permissive schema)
        if "parameters" not in kwargs:
            kwargs["parameters"] = ToolParameter(
                type="object",
                properties={},
                required=[]
            )

        # Call parent Tool.__init__ with filled metadata
        super().__init__(**kwargs)

        # Apply incoming context after model initialization
        if context_value is not None:
            self.context = context_value

        # Keep legacy attribute in sync for runtime hooks
        self._tool_exec_context = self.context_data

    @property
    def context(self) -> Any:
        """Execution context accessor (backward compatibility)."""
        return getattr(self, "context_data", None)

    @context.setter
    def context(self, value: Any) -> None:
        self.context_data = value
        self._tool_exec_context = value


class ToolWrapper:
    """Wrapper to add .name and .description attributes to tool classes/instances for backward compatibility."""

    def __init__(self, tool_or_class):
        self._tool = tool_or_class
        # Add .name attribute - handle both classes and instances
        if hasattr(tool_or_class, '__name__'):
            # It's a class
            self.name = tool_or_class.__name__
        else:
            # It's an instance - use class name
            self.name = tool_or_class.__class__.__name__

        # Add .description attribute from docstring if not present
        if hasattr(tool_or_class, 'description'):
            self.description = tool_or_class.description
        elif tool_or_class.__doc__:
            # Extract first line of docstring as description
            self.description = tool_or_class.__doc__.strip().split('\n')[0]
        else:
            self.description = f"{self.name} tool"

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

        # Separate LeanAgent Tool objects from agency-swarm tools
        lean_tools = []
        agency_tools = []

        for tool in (tools if tools else []):
            # Check if it's a LeanAgent Tool (has Pydantic model structure)
            if isinstance(tool, Tool):
                lean_tools.append(tool)
            else:
                # It's an agency-swarm tool, wrap it
                agency_tools.append(ToolWrapper(tool))

        # Store agency-swarm tools separately for backward compatibility
        self._tools = agency_tools

        # Create config with LeanAgent tools
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
        """Tools folder path (backward compatibility property)."""
        return "tools"  # Default tools folder

    @property
    def model_settings(self) -> dict[str, Any]:
        """Model settings (backward compatibility property)."""
        settings = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        # Add reasoning for GPT-5 models
        if "gpt-5" in self.config.model.lower():
            # Create a simple object with reasoning.summary = "auto"
            class ReasoningSettings:
                summary = "auto"
            settings["reasoning"] = ReasoningSettings()

        return settings


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

        # Validate all agents (allow mocks for testing)
        from unittest.mock import Mock
        for idx, agent in enumerate(agents):
            # Allow real Agent instances or Mock objects (for testing)
            if not isinstance(agent, (Agent, Mock)) and not hasattr(agent, '_spec_class'):
                raise TypeError(
                    f"Agent at position {idx} must be Agent or Mock, got {type(agent).__name__}"
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

            # Prepend to agent instructions (defensive: handle mocks without .config)
            if hasattr(self.agent, 'config') and hasattr(self.agent.config, 'instructions'):
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

    async def get_response(self, message: str, recipient_agent: Agent | None = None) -> str:
        """
        Get response from agent (async alias for backward compatibility).

        Args:
            message: User message
            recipient_agent: Target agent (ignored, we only have one)

        Returns:
            Agent response
        """
        # get_completion is synchronous, but tests expect async
        # Run synchronously and return result
        return self.get_completion(message, recipient_agent)


class SendMessageHandoff(Tool):
    """
    Backward compatibility stub for agency_swarm.tools.SendMessageHandoff.

    In lean architecture, this is a marker class for handoff tools.
    Used in tests and agency orchestration for agent-to-agent communication.
    """

    def __init__(self, **kwargs):
        """Initialize SendMessageHandoff tool (stub for backward compatibility)."""
        # Stub - no actual implementation needed for tests
        pass

    def run(self, **kwargs):
        """Run the handoff tool (stub for backward compatibility)."""
        # Stub - no actual implementation needed for tests
        return "Handoff successful"
