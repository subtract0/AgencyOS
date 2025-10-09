"""
Lean Agent Implementation - Replace Agency Swarm

A minimal, robust agent system that directly uses OpenAI/Anthropic APIs
without the bloat of agency-swarm framework.

Key principles:
- Direct API calls (no framework overhead)
- Simple, predictable behavior
- Easy to debug and maintain
- Type-safe with Pydantic models

Version: 1.0.0
Created: 2025-10-09
"""

import os
from typing import Any, Callable, Optional

from openai import OpenAI
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Parameter definition for a tool."""

    type: str
    properties: dict[str, "ToolPropertySchema"] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class ToolPropertySchema(BaseModel):
    """Schema for a single tool property."""

    type: str
    description: str | None = None
    enum: list[str] | None = None


class OpenAIToolFormat(BaseModel):
    """OpenAI tool format schema."""

    type: str
    function: "FunctionDefinition"


class FunctionDefinition(BaseModel):
    """Function definition in OpenAI format."""

    name: str
    description: str
    parameters: ToolParameter


class Tool(BaseModel):
    """Tool definition for agent."""

    name: str
    description: str
    parameters: ToolParameter
    function: Optional[Callable] = Field(default=None, exclude=True)

    def to_openai_format(self) -> OpenAIToolFormat:
        """Convert to OpenAI tool format."""
        return OpenAIToolFormat(
            type="function",
            function=FunctionDefinition(
                name=self.name,
                description=self.description,
                parameters=self.parameters,
            ),
        )


class AgentConfig(BaseModel):
    """Agent configuration."""

    name: str
    instructions: str
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4000
    tools: list[Tool] = Field(default_factory=list)


class Message(BaseModel):
    """Chat message."""

    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_calls: Optional[list[dict]] = None
    tool_call_id: Optional[str] = None


class LeanAgent:
    """
    Minimal agent implementation using direct OpenAI API.

    This replaces agency_swarm.Agent with a lean, predictable implementation.

    Example:
        >>> agent = LeanAgent(AgentConfig(
        ...     name="coder",
        ...     instructions="You are a Python expert",
        ...     model="gpt-4o"
        ... ))
        >>> response = agent.run("Write a function to add two numbers")
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize agent.

        Args:
            config: Agent configuration
        """
        self.config = config
        self.messages: list[Message] = []
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Add system instructions as first message
        self.messages.append(Message(role="system", content=config.instructions))

    def run(self, user_message: str, max_iterations: int = 10) -> str:
        """
        Execute agent with user message.

        Handles tool calls automatically in a loop until completion.

        Args:
            user_message: User's input message
            max_iterations: Max tool call iterations (prevent infinite loops)

        Returns:
            Final assistant response
        """
        # Add user message
        self.messages.append(Message(role="user", content=user_message))

        # Run agent loop with tool calling
        for iteration in range(max_iterations):
            # Call LLM
            response = self._call_llm()

            # Check if done (no tool calls)
            if not response.tool_calls:
                # Add assistant response and return
                self.messages.append(
                    Message(role="assistant", content=response.content or "")
                )
                return response.content or ""

            # Process tool calls
            self.messages.append(
                Message(
                    role="assistant",
                    content=response.content or "",
                    tool_calls=[tc.model_dump() for tc in response.tool_calls],
                )
            )

            for tool_call in response.tool_calls:
                # Execute tool
                tool_result = self._execute_tool(
                    tool_call.function.name, tool_call.function.arguments
                )

                # Add tool result to messages
                self.messages.append(
                    Message(
                        role="tool", content=str(tool_result), tool_call_id=tool_call.id
                    )
                )

        raise RuntimeError(f"Agent exceeded max iterations ({max_iterations})")

    def _call_llm(self):
        """Call OpenAI API with current messages."""
        # Convert messages to OpenAI format
        openai_messages = []
        for msg in self.messages:
            if msg.role == "tool":
                openai_messages.append(
                    {"role": "tool", "content": msg.content, "tool_call_id": msg.tool_call_id}
                )
            elif msg.tool_calls:
                openai_messages.append(
                    {
                        "role": "assistant",
                        "content": msg.content,
                        "tool_calls": msg.tool_calls,
                    }
                )
            else:
                openai_messages.append({"role": msg.role, "content": msg.content})

        # Prepare tools
        tools = (
            [tool.to_openai_format().model_dump() for tool in self.config.tools]
            if self.config.tools
            else None
        )

        # Call API with model-specific parameters
        call_kwargs = {
            "model": self.config.model,
            "messages": openai_messages,
        }

        # Check if this is an o1/o3/gpt-5 model (reasoning models have restrictions)
        is_reasoning_model = any(m in self.config.model.lower() for m in ["o1", "o3", "gpt-5"])

        if is_reasoning_model:
            # Reasoning models don't support temperature, tools, or max_tokens
            # They use max_completion_tokens and default temperature=1
            call_kwargs["max_completion_tokens"] = self.config.max_tokens
        else:
            # Standard models support all parameters
            call_kwargs["temperature"] = self.config.temperature
            call_kwargs["max_tokens"] = self.config.max_tokens
            if tools:
                call_kwargs["tools"] = tools

        response = self.client.chat.completions.create(**call_kwargs)

        return response.choices[0].message

    def _execute_tool(self, tool_name: str, arguments: str) -> str:
        """
        Execute a tool call.

        Args:
            tool_name: Name of tool to execute
            arguments: JSON string of arguments

        Returns:
            Tool execution result
        """
        import json

        # Find tool
        tool = next((t for t in self.config.tools if t.name == tool_name), None)
        if not tool:
            return f"Error: Tool '{tool_name}' not found"

        if not tool.function:
            return f"Error: Tool '{tool_name}' has no function"

        # Parse arguments
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError as e:
            return f"Error: Invalid arguments JSON: {e}"

        # Execute function
        try:
            result = tool.function(**args)
            return str(result)
        except Exception as e:
            return f"Error executing {tool_name}: {e}"

    def clear_history(self):
        """Clear message history (keep system prompt)."""
        system_msg = self.messages[0]
        self.messages = [system_msg]


# Helper function to create tool from Python function
def tool(name: str, description: str, parameters: ToolParameter):
    """
    Decorator to convert Python function to Tool.

    Example:
        >>> param = ToolParameter(
        ...     type="object",
        ...     properties={
        ...         "a": ToolPropertySchema(type="number"),
        ...         "b": ToolPropertySchema(type="number")
        ...     },
        ...     required=["a", "b"]
        ... )
        >>> @tool("add", "Add two numbers", param)
        ... def add(a: float, b: float) -> float:
        ...     return a + b
    """

    def decorator(func: Callable) -> Tool:
        return Tool(name=name, description=description, parameters=parameters, function=func)

    return decorator
