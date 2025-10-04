# Connect Claude Code to tools via MCP

The Model Context Protocol (MCP) lets Claude Code integrate with external tools, data sources, and services. Think of MCP as a plugin system—servers expose capabilities (tools, resources, prompts), and Claude Code consumes them seamlessly.

## What is MCP?

MCP is an open protocol for connecting AI assistants to external systems. Instead of hardcoding integrations, you configure **MCP servers** that provide:

- **Tools**: Functions Claude can call (e.g., `search_database`, `send_email`).
- **Resources**: Data sources Claude can read (e.g., files, APIs, databases).
- **Prompts**: Pre-built prompt templates (e.g., "summarize this document").

Claude Code uses MCP to extend its capabilities beyond built-in tools.

## Why use MCP?

### Use cases

1. **Custom tools**: Add project-specific commands (e.g., deploy to staging, run custom linters).
2. **Data access**: Let Claude query databases, APIs, or internal services.
3. **Third-party integrations**: Connect to GitHub, Slack, Jira, etc.
4. **Domain expertise**: Provide specialized tools (e.g., legal document analysis, CAD operations).

### Benefits

- **Modular**: Enable/disable integrations without code changes.
- **Reusable**: Share MCP servers across projects and teams.
- **Secure**: Servers run locally or in controlled environments (no data leaves your network).
- **Standard**: MCP is open—works with any MCP-compatible AI assistant.

## How MCP works

```
Claude Code  <--> MCP Client  <--> MCP Server  <--> External System
                                     (stdio)         (DB, API, etc.)
```

1. **MCP Server**: Exposes tools/resources via stdio (JSON-RPC protocol).
2. **MCP Client** (built into Claude Code): Discovers and calls server capabilities.
3. **Claude Code**: Uses MCP tools like built-in tools (transparent to the user).

## Setting up MCP

### 1. Install an MCP server

Example: Official filesystem server (lets Claude access local files).

```bash
npm install -g @modelcontextprotocol/server-filesystem
```

### 2. Configure Claude Code

Add to `.claude/config.json`:

```json
{
  "mcp": {
    "servers": {
      "filesystem": {
        "command": "mcp-server-filesystem",
        "args": ["/path/to/allowed/directory"],
        "env": {}
      }
    }
  }
}
```

### 3. Verify connection

```bash
claude-code --debug
# Look for: [MCP] Connected to server 'filesystem' (3 tools, 1 resource)
```

### 4. Use MCP tools

Ask Claude Code to use the new tools:

```
List all markdown files in the project.
```

Claude will use `mcp__filesystem__list_files` (the MCP tool) automatically.

## Available MCP servers

### Official servers

| Server              | Description                | Install                                            |
| ------------------- | -------------------------- | -------------------------------------------------- |
| `server-filesystem` | Local file access          | `npm i -g @modelcontextprotocol/server-filesystem` |
| `server-github`     | GitHub API integration     | `npm i -g @modelcontextprotocol/server-github`     |
| `server-postgres`   | PostgreSQL queries         | `npm i -g @modelcontextprotocol/server-postgres`   |
| `server-slack`      | Slack messaging            | `npm i -g @modelcontextprotocol/server-slack`      |
| `server-memory`     | Persistent key-value store | `npm i -g @modelcontextprotocol/server-memory`     |

### Community servers

Browse the [MCP server registry](https://github.com/modelcontextprotocol/servers) for more.

## Configuration examples

### GitHub integration

```json
{
  "mcp": {
    "servers": {
      "github": {
        "command": "mcp-server-github",
        "env": {
          "GITHUB_TOKEN": "ghp_your_token_here"
        }
      }
    }
  }
}
```

**Usage:**

```
Create a GitHub issue titled "Fix login bug" in repo my-org/my-repo.
```

### PostgreSQL access

```json
{
  "mcp": {
    "servers": {
      "postgres": {
        "command": "mcp-server-postgres",
        "args": ["postgresql://user:pass@localhost/mydb"]
      }
    }
  }
}
```

**Usage:**

```
Query the database: SELECT * FROM users WHERE created_at > '2024-01-01';
```

### Slack notifications

```json
{
  "mcp": {
    "servers": {
      "slack": {
        "command": "mcp-server-slack",
        "env": {
          "SLACK_TOKEN": "xoxb-your-token"
        }
      }
    }
  }
}
```

**Usage:**

```
Send a Slack message to #engineering: "Deploy complete."
```

## Building a custom MCP server

### Minimal example (Python)

```python
# my_tools_server.py
from mcp.server import MCPServer, Tool

server = MCPServer("my-tools")

@server.tool()
async def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

@server.tool()
async def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

if __name__ == "__main__":
    server.run()
```

### Configuration

```json
{
  "mcp": {
    "servers": {
      "my-tools": {
        "command": "python",
        "args": ["/path/to/my_tools_server.py"]
      }
    }
  }
}
```

### Usage

```
Use the greet tool to say hello to Alice.
```

Claude Code will call `mcp__my-tools__greet(name="Alice")`.

## Advanced features

### Environment variables

Pass secrets securely:

```json
{
  "mcp": {
    "servers": {
      "api-client": {
        "command": "mcp-server-api",
        "env": {
          "API_KEY": "${API_KEY}",
          "API_URL": "https://api.example.com"
        }
      }
    }
  }
}
```

Set `API_KEY` in your shell before running Claude Code.

### Multiple servers

Load multiple MCP servers simultaneously:

```json
{
  "mcp": {
    "servers": {
      "github": { "command": "mcp-server-github" },
      "slack": { "command": "mcp-server-slack" },
      "postgres": { "command": "mcp-server-postgres", "args": ["..."] }
    }
  }
}
```

Claude Code will have access to all tools from all servers.

### Resource subscriptions

Some servers provide **resources** (read-only data):

```python
# Server side
@server.resource("project://config")
async def get_config() -> dict:
    return {"env": "production", "version": "1.2.3"}
```

Claude Code can request this resource:

```
What's the current project configuration?
```

### Server lifecycle

MCP servers start when Claude Code launches and stop on exit. For long-running servers, use a process manager (e.g., systemd, pm2).

## Best practices

### 1. Scope server permissions

Limit file access, API scopes, and database permissions:

```json
{
  "filesystem": {
    "args": ["/safe/directory/only"]
  }
}
```

### 2. Use environment variables for secrets

Never hardcode tokens in config:

```json
{
  "env": {
    "GITHUB_TOKEN": "${GITHUB_TOKEN}"
  }
}
```

### 3. Test servers independently

Before configuring in Claude Code, test servers manually:

```bash
mcp-server-github --help
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | mcp-server-github
```

### 4. Monitor server logs

Run with `--debug` to see MCP communication:

```bash
claude-code --debug
# [MCP] -> tools/call {"name": "greet", "args": {"name": "Alice"}}
# [MCP] <- {"result": "Hello, Alice!"}
```

### 5. Handle server failures gracefully

If an MCP server crashes, Claude Code will log the error and continue with built-in tools.

## Troubleshooting

### Server won't start

**Check:**

- Is the command in PATH? (`which mcp-server-github`)
- Are args/env vars correct?
- Run the command manually to see errors.

### Tools not appearing

**Debug:**

```bash
claude-code --debug
# Look for: [MCP] Discovered tools: mcp__server-name__tool-name
```

### Permission errors

MCP servers inherit Claude Code's permissions. If a server can't access a file, neither can Claude Code.

### Slow responses

MCP calls are synchronous—slow servers block Claude Code. Optimize server performance or use async operations.

## Security considerations

### 1. Trust server code

MCP servers run with your user's permissions. Only use trusted servers (official or vetted community servers).

### 2. Isolate sensitive servers

For servers accessing production databases/APIs, run Claude Code in a restricted environment (Docker, VM, separate user account).

### 3. Audit tool calls

Use [hooks](./hooks-getting-started.md) to log all MCP tool calls:

```python
def pre_tool_hook(tool_name, args, context):
    if tool_name.startswith("mcp__"):
        log_audit(f"MCP call: {tool_name} with {args}")
    return args
```

### 4. Limit network access

If an MCP server doesn't need internet, block it with a firewall.

## MCP vs. built-in tools

| Feature       | Built-in Tools      | MCP Tools                      |
| ------------- | ------------------- | ------------------------------ |
| Setup         | None (ready to use) | Requires server install/config |
| Performance   | Fast (in-process)   | Slower (IPC overhead)          |
| Customization | Hardcoded           | Fully customizable             |
| Security      | Trusted             | Depends on server              |
| Use case      | General tasks       | Project-specific/integrations  |

**Rule of thumb:** Use built-in tools for common operations (file I/O, git, bash). Use MCP for custom/external integrations.

## Example: End-to-end workflow

### Goal

Let Claude Code query a company database and create GitHub issues for findings.

### Setup

1. **Install servers:**

   ```bash
   npm install -g @modelcontextprotocol/server-postgres
   npm install -g @modelcontextprotocol/server-github
   ```

2. **Configure `.claude/config.json`:**

   ```json
   {
     "mcp": {
       "servers": {
         "db": {
           "command": "mcp-server-postgres",
           "args": ["postgresql://user:pass@localhost/company_db"]
         },
         "github": {
           "command": "mcp-server-github",
           "env": {
             "GITHUB_TOKEN": "${GITHUB_TOKEN}"
           }
         }
       }
     }
   }
   ```

3. **Set environment variable:**

   ```bash
   export GITHUB_TOKEN=ghp_your_token
   ```

### Usage

```
Query the database for all users created in the last 7 days.
For each user, create a GitHub issue in my-org/onboarding-tasks with title "Onboard {user.name}".
```

**Claude Code will:**

1. Call `mcp__db__query("SELECT * FROM users WHERE created_at > NOW() - INTERVAL '7 days'")`
2. For each result, call `mcp__github__create_issue(repo="my-org/onboarding-tasks", title="Onboard Alice")`

All without manual API calls or scripts.

## FAQ

**Q: Do MCP servers require internet?**
A: No. MCP uses stdio (local communication). Servers only need internet if they access external APIs.

**Q: Can I use MCP with headless mode?**
A: Yes. MCP works in all modes (CLI, headless, server).

**Q: How do I update MCP servers?**
A: Re-run the install command (`npm install -g @modelcontextprotocol/server-xyz`).

**Q: Can MCP servers share state?**
A: Not directly. Use external storage (files, databases, Redis) for inter-server communication.

**Q: Is MCP secure?**
A: MCP itself is a protocol—security depends on server implementation. Audit server code before use.

**Q: Can I disable MCP temporarily?**
A: Remove the `"mcp"` section from `.claude/config.json` or use `--no-mcp` flag.

---

**Next steps:**

- Install an official MCP server (`server-filesystem` is a good start).
- Build a custom server for a project-specific workflow.
- Combine MCP with [hooks](./hooks-getting-started.md) for advanced automation.
