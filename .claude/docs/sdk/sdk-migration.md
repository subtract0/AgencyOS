# Migrate to Claude Agent SDK

This guide helps you migrate from direct Claude API usage to the Claude Agent SDK, which provides built-in support for tool use, extended thinking, and agentic workflows.

## Why Migrate?

The Claude Agent SDK provides:

- **Built-in tool support**: File operations, shell commands, and custom tools
- **Extended thinking**: Access to Claude's internal reasoning process
- **Session management**: Automatic conversation context handling
- **MCP integration**: Easy integration with Model Context Protocol servers
- **Streaming support**: Stream responses for better UX
- **Permission control**: Fine-grained control over tool usage

## Migration Steps

### 1. Before: Direct API Usage

```python
import anthropic

client = anthropic.Anthropic(api_key="your-api-key")

response = client.messages.create(
    model="claude-opus-4-20250514",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ]
)

print(response.content[0].text)
```

### 1. After: SDK Usage

```python
from claude_agent_sdk import query, ClaudeAgentOptions

response = await query(
    prompt="What is the capital of France?",
    api_key="your-api-key",
    options=ClaudeAgentOptions(
        model="claude-opus-4-20250514",
        max_tokens=1024
    )
)

print(response.output_text)
```

### 2. Before: Multi-turn Conversations

```python
conversation = []

# First turn
conversation.append({"role": "user", "content": "What is 2+2?"})
response = client.messages.create(
    model="claude-opus-4-20250514",
    max_tokens=1024,
    messages=conversation
)
conversation.append({"role": "assistant", "content": response.content[0].text})

# Second turn
conversation.append({"role": "user", "content": "What about multiplying that by 3?"})
response = client.messages.create(
    model="claude-opus-4-20250514",
    max_tokens=1024,
    messages=conversation
)
```

### 2. After: Automatic Session Management

```python
from claude_agent_sdk import ClaudeAgentClient, ClaudeAgentOptions

client = ClaudeAgentClient(
    api_key="your-api-key",
    options=ClaudeAgentOptions(model="claude-opus-4-20250514")
)

# First turn
response1 = await client.send("What is 2+2?")
print(response1.output_text)

# Second turn (context automatically maintained)
response2 = await client.send("What about multiplying that by 3?")
print(response2.output_text)
```

### 3. Before: Tool Use

```python
tools = [{
    "name": "get_weather",
    "description": "Get weather for a location",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {"type": "string"}
        }
    }
}]

response = client.messages.create(
    model="claude-opus-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather in Paris?"}]
)

# Manually handle tool calls
if response.stop_reason == "tool_use":
    for tool_use in response.content:
        if tool_use.type == "tool_use":
            # Execute tool manually
            result = get_weather(tool_use.input)
            # Send result back manually...
```

### 3. After: Automatic Tool Handling

```python
from claude_agent_sdk import ClaudeAgentClient, ClaudeAgentOptions, tool

@tool(
    name="get_weather",
    description="Get weather for a location",
    input_schema={
        "type": "object",
        "properties": {
            "location": {"type": "string"}
        }
    }
)
async def get_weather(args):
    # Tool implementation
    return {
        "content": [{
            "type": "text",
            "text": f"Weather in {args['location']}: Sunny"
        }]
    }

client = ClaudeAgentClient(
    api_key="your-api-key",
    options=ClaudeAgentOptions(
        custom_tools=[get_weather],
        permission_mode="accept_all"
    )
)

# Tool is automatically called and result integrated
response = await client.send("What's the weather in Paris?")
print(response.output_text)
```

### 4. Before: Streaming

```python
with client.messages.stream(
    model="claude-opus-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### 4. After: SDK Streaming

```python
from claude_agent_sdk import ClaudeAgentClient

client = ClaudeAgentClient(api_key="your-api-key")

async for chunk in client.stream("Write a story"):
    if chunk.type == "text":
        print(chunk.text, end="", flush=True)
    elif chunk.type == "thinking":
        print(f"\n[Thinking: {chunk.thinking}]")
```

## Feature Mapping

| Direct API            | SDK Equivalent    | Notes                         |
| --------------------- | ----------------- | ----------------------------- |
| `messages.create()`   | `client.send()`   | One-off queries use `query()` |
| Manual message list   | `client.send()`   | Auto-managed history          |
| `tools` parameter     | `custom_tools`    | Use `@tool` decorator         |
| `stream()`            | `client.stream()` | Enhanced with thinking        |
| Manual tool execution | Automatic         | Set `permission_mode`         |
| N/A                   | Extended thinking | New capability                |
| N/A                   | MCP servers       | New capability                |

## Extended Thinking (New Feature)

One of the key benefits of the SDK is access to extended thinking:

```python
options = ClaudeAgentOptions(
    thinking={
        "type": "enabled",
        "budget_tokens": 10000
    }
)

client = ClaudeAgentClient(api_key="your-api-key", options=options)

response = await client.send("Solve this complex problem...")

# Access the thinking process
if response.thinking:
    print(f"Claude's reasoning: {response.thinking}")
```

## MCP Integration (New Feature)

Easily integrate Model Context Protocol servers:

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
        }
    },
    allowed_tools=["mcp__filesystem__read"]
)

client = ClaudeAgentClient(api_key="your-api-key", options=options)
```

## Permission Modes (New Feature)

Control tool usage with permission modes:

```python
options = ClaudeAgentOptions(
    permission_mode="accept_edits"  # Auto-accept file edits
)

# Other modes: "accept_all", "prompt", "reject_all"
```

## Migration Checklist

- [ ] Install `claude-agent-sdk` package
- [ ] Replace `anthropic.Anthropic()` with `ClaudeAgentClient()`
- [ ] Convert manual conversation management to `client.send()`
- [ ] Convert tool definitions to `@tool` decorators
- [ ] Update streaming to use `client.stream()`
- [ ] Set appropriate `permission_mode` for your use case
- [ ] Enable extended thinking for complex tasks
- [ ] Add MCP servers if needed
- [ ] Update error handling to catch `ClaudeAgentError`
- [ ] Test all functionality

## Common Patterns

### Pattern 1: Simple Query

**Before:**

```python
response = client.messages.create(
    model="claude-opus-4-20250514",
    messages=[{"role": "user", "content": prompt}]
)
answer = response.content[0].text
```

**After:**

```python
response = await query(prompt, api_key="your-api-key")
answer = response.output_text
```

### Pattern 2: Conversation Loop

**Before:**

```python
messages = []
while True:
    user_input = input("You: ")
    messages.append({"role": "user", "content": user_input})
    response = client.messages.create(model="...", messages=messages)
    assistant_message = response.content[0].text
    messages.append({"role": "assistant", "content": assistant_message})
    print(f"Assistant: {assistant_message}")
```

**After:**

```python
client = ClaudeAgentClient(api_key="your-api-key")
while True:
    user_input = input("You: ")
    response = await client.send(user_input)
    print(f"Assistant: {response.output_text}")
```

### Pattern 3: File Operations Tool

**Before:**

```python
# Define tool schema
# Handle tool calls manually
# Execute file operations
# Return results
# Continue conversation
```

**After:**

```python
# Built-in file tools available automatically
options = ClaudeAgentOptions(
    allowed_tools=["read", "write", "edit"],
    permission_mode="accept_edits"
)
client = ClaudeAgentClient(api_key="your-api-key", options=options)
```

## Troubleshooting

### Issue: Async/Await Required

The SDK uses async/await. If you're migrating from sync code:

```python
import asyncio

async def main():
    response = await query("Your prompt")
    print(response.output_text)

asyncio.run(main())
```

### Issue: Tool Permissions

If tools aren't being used:

1. Check `allowed_tools` includes your tool name
2. Set appropriate `permission_mode`
3. Verify tool schema is correct

### Issue: Missing Context

If conversation context isn't working:

1. Use the same `ClaudeAgentClient` instance
2. Don't call `clear_history()` between turns
3. Check you're using `send()` not `query()`

## Next Steps

- Read the [Python SDK Reference](./python-sdk-reference.md)
- Explore [MCP servers](https://modelcontextprotocol.io/)
- Review [extended thinking documentation](https://docs.anthropic.com/extended-thinking)
- Join the [Discord community](https://discord.gg/anthropic)

## Getting Help

- SDK Issues: [GitHub Issues](https://github.com/anthropics/claude-agent-sdk-python/issues)
- API Questions: [Support](https://support.anthropic.com/)
- Community: [Discord](https://discord.gg/anthropic)
