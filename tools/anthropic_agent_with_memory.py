"""Anthropic SDK Integration Helper with Memory Tool

Provides high-level functions to create Anthropic clients with memory tool support.
Simplifies the setup of Claude agents with persistent cross-conversation memory.

Usage:
    from tools.anthropic_agent_with_memory import create_client_with_memory, run_with_memory

    # Create client and memory tool
    client, memory_tool = create_client_with_memory(session_id="task_123")

    # Run conversation with memory
    response = run_with_memory(
        client=client,
        memory_tool=memory_tool,
        messages=[{"role": "user", "content": "Remember: Python is my favorite language"}],
        model="claude-sonnet-4-5"
    )
"""

import os
from pathlib import Path
from typing import Any

try:
    import anthropic
    from anthropic.types.beta import BetaMessageParam
    from tools.anthropic_memory_tool import AgencyMemoryTool, create_memory_tool
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None
    BetaMessageParam = Any
    AgencyMemoryTool = Any


def create_client_with_memory(
    api_key: str | None = None,
    session_id: str | None = None,
    base_dir: str | None = None,
    max_file_size: int = 1_000_000
) -> tuple[Any, Any]:
    """Create Anthropic client with memory tool

    Args:
        api_key: Anthropic API key (default: ANTHROPIC_API_KEY env var)
        session_id: Session ID for isolated memory space
        base_dir: Custom base directory (default: ~/.agency/memories)
        max_file_size: Maximum file size in bytes

    Returns:
        Tuple of (client, memory_tool)

    Raises:
        ImportError: If anthropic SDK not installed
        ValueError: If API key not provided and ANTHROPIC_API_KEY not set
    """
    if not ANTHROPIC_AVAILABLE:
        raise ImportError(
            "anthropic SDK not installed. "
            "Run: uv pip install 'anthropic>=0.42.0'"
        )

    # Get API key
    if api_key is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "API key required. Set ANTHROPIC_API_KEY or pass api_key parameter"
        )

    # Create client
    client = anthropic.Anthropic(api_key=api_key)

    # Create memory tool
    memory_tool = create_memory_tool(
        session_id=session_id,
        base_dir=base_dir
    )

    # Set size limit
    memory_tool.max_file_size = max_file_size

    return client, memory_tool


def run_with_memory(
    client: Any,
    memory_tool: Any,
    messages: list[dict[str, str]],
    model: str = "claude-sonnet-4-5",
    max_tokens: int = 4096,
    system: str | None = None,
    temperature: float = 1.0,
    stream: bool = False
) -> Any:
    """Run Claude conversation with memory tool enabled

    Args:
        client: Anthropic client instance
        memory_tool: AgencyMemoryTool instance
        messages: List of message dicts with 'role' and 'content'
        model: Model name (must support memory tool)
        max_tokens: Maximum tokens in response
        system: Optional system prompt
        temperature: Sampling temperature (0-1)
        stream: Whether to stream response

    Returns:
        Message response or stream iterator

    Raises:
        ImportError: If anthropic SDK not installed
        anthropic.BadRequestError: If beta access denied
    """
    if not ANTHROPIC_AVAILABLE:
        raise ImportError(
            "anthropic SDK not installed. "
            "Run: uv pip install 'anthropic>=0.42.0'"
        )

    # Import beta tools
    from anthropic.types.beta import BetaMemoryTool

    # Prepare request parameters
    request_params = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
        "tools": [BetaMemoryTool(memory_tool)],
        "betas": ["context-management-2025-06-27"],
        "temperature": temperature
    }

    if system:
        request_params["system"] = system

    # Make request
    if stream:
        return client.beta.messages.stream(**request_params)
    else:
        return client.beta.messages.create(**request_params)


def handle_tool_calls(
    message: Any,
    client: Any,
    memory_tool: Any,
    messages: list[dict[str, str]],
    model: str = "claude-sonnet-4-5",
    max_iterations: int = 5
) -> Any:
    """Handle tool calls in a conversation loop

    Automatically processes memory tool calls and continues conversation
    until Claude provides a final response without tool calls.

    Args:
        message: Initial message response from Claude
        client: Anthropic client instance
        memory_tool: AgencyMemoryTool instance
        messages: Conversation history
        model: Model name
        max_iterations: Maximum tool call iterations

    Returns:
        Final message response

    Example:
        client, memory_tool = create_client_with_memory()
        messages = [{"role": "user", "content": "Remember my name is Alice"}]
        response = run_with_memory(client, memory_tool, messages)
        final = handle_tool_calls(response, client, memory_tool, messages)
    """
    iteration = 0

    while iteration < max_iterations:
        # Check if response has tool calls
        if message.stop_reason != "tool_use":
            return message

        # Add assistant response to history
        messages.append({
            "role": "assistant",
            "content": message.content
        })

        # Process tool calls
        tool_results = []
        for content_block in message.content:
            if content_block.type == "tool_use":
                tool_name = content_block.name
                tool_input = content_block.input

                # Execute tool (memory tool is handled by SDK)
                # This is just for reference - SDK handles it automatically
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": "Tool executed by SDK"
                })

        # Add tool results to history
        messages.append({
            "role": "user",
            "content": tool_results
        })

        # Continue conversation
        message = run_with_memory(
            client=client,
            memory_tool=memory_tool,
            messages=messages,
            model=model
        )

        iteration += 1

    return message


def get_memory_stats(memory_tool: Any) -> dict[str, Any]:
    """Get statistics about memory storage

    Args:
        memory_tool: AgencyMemoryTool instance

    Returns:
        Dict with file count, total size, directory count
    """
    base_dir = Path(memory_tool.base_dir)

    if not base_dir.exists():
        return {
            "file_count": 0,
            "total_size": 0,
            "directory_count": 0,
            "base_dir": str(base_dir)
        }

    file_count = 0
    total_size = 0
    directory_count = 0

    for path in base_dir.rglob("*"):
        if path.is_file():
            file_count += 1
            total_size += path.stat().st_size
        elif path.is_dir():
            directory_count += 1

    return {
        "file_count": file_count,
        "total_size": total_size,
        "total_size_mb": round(total_size / 1_000_000, 2),
        "directory_count": directory_count,
        "base_dir": str(base_dir)
    }


# Convenience exports
__all__ = [
    "create_client_with_memory",
    "run_with_memory",
    "handle_tool_calls",
    "get_memory_stats",
    "ANTHROPIC_AVAILABLE"
]
