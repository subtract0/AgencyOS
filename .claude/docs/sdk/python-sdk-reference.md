# Agent SDK reference - Python

The Claude Agent SDK for Python provides tools for building autonomous agents that can use Claude's extended thinking mode, tool use, and other advanced features.

## Installation

```bash
pip install claude-agent-sdk
```

## Core Components

### ClaudeAgentClient

The main client for interacting with Claude agents.

```python
from claude_agent_sdk import ClaudeAgentClient, ClaudeAgentOptions

client = ClaudeAgentClient(
    api_key="your-api-key",
    options=ClaudeAgentOptions(
        model="claude-opus-4-20250514",
        max_tokens=4096,
        temperature=1.0
    )
)
```

### ClaudeAgentOptions

Configuration options for the agent.

```python
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    model="claude-opus-4-20250514",  # Model to use
    max_tokens=4096,                  # Maximum tokens to generate
    temperature=1.0,                  # Sampling temperature
    mcp_servers={},                   # MCP servers configuration
    allowed_tools=[],                 # List of allowed tool names
    permission_mode="accept_edits",   # Permission handling mode
    thinking={                        # Extended thinking configuration
        "type": "enabled",
        "budget_tokens": 10000
    }
)
```

#### Permission Modes

- `"accept_edits"`: Automatically accept file edits
- `"accept_all"`: Accept all tool uses
- `"prompt"`: Prompt for each tool use (default)
- `"reject_all"`: Reject all tool uses

### query()

One-off query to Claude without maintaining conversation state.

```python
from claude_agent_sdk import query, ClaudeAgentOptions

response = await query(
    prompt="What is the capital of France?",
    api_key="your-api-key",
    options=ClaudeAgentOptions(
        model="claude-opus-4-20250514"
    )
)

print(response.output_text)
```

### Streaming Responses

```python
async for chunk in client.stream("Write a story"):
    if chunk.type == "text":
        print(chunk.text, end="", flush=True)
    elif chunk.type == "thinking":
        print(f"\n[Thinking: {chunk.thinking}]")
```

## Tools

### Built-in Tools

The SDK includes several built-in tools:

- `read`: Read file contents
- `write`: Write to files
- `edit`: Edit files
- `glob`: Find files by pattern
- `grep`: Search file contents
- `bash`: Execute shell commands

### Custom Tools

Create custom tools using the `@tool` decorator:

```python
from claude_agent_sdk import tool

@tool(
    name="calculate",
    description="Perform arithmetic calculations",
    input_schema={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Math expression to evaluate"
            }
        },
        "required": ["expression"]
    }
)
async def calculate(args):
    result = eval(args["expression"])  # Note: Use safely in production
    return {
        "content": [{
            "type": "text",
            "text": f"Result: {result}"
        }]
    }

# Use in client
client = ClaudeAgentClient(
    api_key="your-api-key",
    options=ClaudeAgentOptions(
        custom_tools=[calculate]
    )
)
```

### MCP Servers

Integrate Model Context Protocol servers:

```python
from claude_agent_sdk import ClaudeAgentClient, ClaudeAgentOptions

options = ClaudeAgentOptions(
    mcp_servers={
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"]
        }
    },
    allowed_tools=["mcp__filesystem__read", "mcp__filesystem__write"]
)

client = ClaudeAgentClient(api_key="your-api-key", options=options)
```

## Extended Thinking

Enable extended thinking for complex reasoning tasks:

```python
options = ClaudeAgentOptions(
    thinking={
        "type": "enabled",
        "budget_tokens": 10000
    }
)

response = await client.send("Solve this complex problem...")

# Access thinking process
if response.thinking:
    print(f"Thinking: {response.thinking}")
```

## Session Management

Maintain conversation context across multiple turns:

```python
client = ClaudeAgentClient(api_key="your-api-key")

# First turn
response1 = await client.send("What is 2+2?")
print(response1.output_text)  # "4"

# Second turn (context maintained)
response2 = await client.send("What about multiplying that by 3?")
print(response2.output_text)  # "12"

# Clear conversation history
client.clear_history()
```

## Error Handling

```python
from claude_agent_sdk import ClaudeAgentError

try:
    response = await client.send("Your prompt")
except ClaudeAgentError as e:
    print(f"Agent error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Complete Example

```python
import asyncio
from claude_agent_sdk import ClaudeAgentClient, ClaudeAgentOptions, tool

@tool(
    name="get_weather",
    description="Get weather for a location",
    input_schema={
        "type": "object",
        "properties": {
            "location": {"type": "string"}
        },
        "required": ["location"]
    }
)
async def get_weather(args):
    # Simulated weather lookup
    return {
        "content": [{
            "type": "text",
            "text": f"Weather in {args['location']}: Sunny, 72°F"
        }]
    }

async def main():
    client = ClaudeAgentClient(
        api_key="your-api-key",
        options=ClaudeAgentOptions(
            model="claude-opus-4-20250514",
            custom_tools=[get_weather],
            permission_mode="accept_all",
            thinking={
                "type": "enabled",
                "budget_tokens": 5000
            }
        )
    )

    # Stream response
    async for chunk in client.stream("What's the weather in Paris?"):
        if chunk.type == "text":
            print(chunk.text, end="", flush=True)
        elif chunk.type == "thinking":
            print(f"\n[Thinking: {chunk.thinking}]")

    print()

if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

### ClaudeAgentClient Methods

- `send(prompt: str) -> Response`: Send a message and wait for response
- `stream(prompt: str) -> AsyncIterator[Chunk]`: Stream response chunks
- `clear_history()`: Clear conversation history
- `get_history() -> List[Message]`: Get conversation history

### Response Object

- `output_text: str`: The text response
- `thinking: Optional[str]`: Extended thinking content
- `tool_uses: List[ToolUse]`: Tools used during response
- `stop_reason: str`: Why generation stopped

### Chunk Types

- `text`: Text content chunk
- `thinking`: Extended thinking chunk
- `tool_use`: Tool usage chunk
- `tool_result`: Tool result chunk

## Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `CLAUDE_AGENT_MODEL`: Default model to use
- `CLAUDE_AGENT_MAX_TOKENS`: Default max tokens

## Best Practices

1. **Use Extended Thinking**: Enable for complex reasoning tasks
2. **Set Permission Modes**: Use `accept_edits` in automated environments
3. **Handle Errors**: Always wrap API calls in try-catch
4. **Stream Responses**: Use streaming for better UX
5. **Clear History**: Clear when starting new tasks
6. **Tool Safety**: Validate tool inputs and outputs
7. **Rate Limiting**: Implement backoff for production use

## Further Reading

- [Migration Guide](./sdk-migration.md)
- [MCP Documentation](https://modelcontextprotocol.io/)
- [Claude API Documentation](https://docs.anthropic.com/)
