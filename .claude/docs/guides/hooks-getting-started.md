# Get started with Claude Code hooks

Hooks let you inject custom logic into Claude Code's execution flow. Think of them as middleware—you define functions that run at specific lifecycle events (before tools execute, after responses, on errors, etc.). Use hooks to add logging, validation, telemetry, or custom workflows without modifying core code.

## What are hooks?

Hooks are user-defined functions that Claude Code calls at predefined points:

- **Pre-tool hooks**: Run before a tool executes (validate inputs, log intent).
- **Post-tool hooks**: Run after a tool executes (audit results, trigger side effects).
- **Response hooks**: Run after Claude generates a response (analyze output, save context).
- **Error hooks**: Run when exceptions occur (custom error handling, retry logic).

Hooks are **optional** and **composable**—enable only what you need.

## Why use hooks?

### Use cases

1. **Telemetry**: Track tool usage, response times, error rates.
2. **Validation**: Enforce policies (e.g., block `rm -rf /` commands).
3. **Auditing**: Log all file changes for compliance.
4. **Custom workflows**: Auto-commit after successful test runs.
5. **Debugging**: Inspect tool inputs/outputs in real time.

### Example: Auto-commit hook

```python
# .claude/hooks/auto_commit.py
def post_tool_hook(tool_name, result, context):
    """Auto-commit after successful test runs."""
    if tool_name == "Bash" and "pytest" in context.get("command", ""):
        if result.get("exit_code") == 0:
            context["git"].commit("test: Passing test suite")
```

## Hook types

### 1. Pre-tool hooks

Run **before** a tool executes.

**Signature:**

```python
def pre_tool_hook(tool_name: str, args: dict, context: dict) -> dict | None:
    """
    Args:
        tool_name: Name of the tool about to run (e.g., "Bash", "Edit").
        args: Tool arguments (e.g., {"command": "ls -la"}).
        context: Execution context (cwd, env vars, session state).

    Returns:
        Modified args dict (or None to proceed unchanged).
        Raise exception to abort tool execution.
    """
    pass
```

**Example: Validate Bash commands**

```python
def pre_tool_hook(tool_name, args, context):
    if tool_name == "Bash":
        cmd = args.get("command", "")
        if "rm -rf /" in cmd:
            raise ValueError("Dangerous command blocked")
    return args
```

### 2. Post-tool hooks

Run **after** a tool executes.

**Signature:**

```python
def post_tool_hook(tool_name: str, result: dict, context: dict) -> None:
    """
    Args:
        tool_name: Name of the tool that just ran.
        result: Tool output (e.g., {"stdout": "...", "exit_code": 0}).
        context: Execution context (updated with tool effects).

    Returns:
        None (side effects only—result is not modified).
    """
    pass
```

**Example: Log file edits**

```python
def post_tool_hook(tool_name, result, context):
    if tool_name == "Edit":
        with open(".claude/audit.log", "a") as f:
            f.write(f"Edited {result['file_path']} at {context['timestamp']}\n")
```

### 3. Response hooks

Run **after** Claude generates a response.

**Signature:**

```python
def response_hook(response: str, context: dict) -> None:
    """
    Args:
        response: Claude's generated response text.
        context: Execution context (includes tool results, session state).

    Returns:
        None (side effects only—response is not modified).
    """
    pass
```

**Example: Save responses to file**

```python
def response_hook(response, context):
    with open(".claude/responses.jsonl", "a") as f:
        f.write(json.dumps({"response": response, "timestamp": time.time()}) + "\n")
```

### 4. Error hooks

Run **when exceptions occur**.

**Signature:**

```python
def error_hook(error: Exception, context: dict) -> None:
    """
    Args:
        error: The exception that was raised.
        context: Execution context at time of error.

    Returns:
        None (can log, alert, or re-raise).
    """
    pass
```

**Example: Send error alerts**

```python
def error_hook(error, context):
    if isinstance(error, PermissionError):
        send_slack_alert(f"Permission error in {context['cwd']}: {error}")
```

## Setting up hooks

### 1. Create a hooks file

Create `.claude/hooks/my_hooks.py`:

```python
# .claude/hooks/my_hooks.py

def pre_tool_hook(tool_name, args, context):
    print(f"[HOOK] About to run {tool_name}")
    return args

def post_tool_hook(tool_name, result, context):
    print(f"[HOOK] Finished {tool_name}")

def response_hook(response, context):
    print(f"[HOOK] Response length: {len(response)} chars")

def error_hook(error, context):
    print(f"[HOOK] Error: {error}")
```

### 2. Enable hooks in config

Add to `.claude/config.json`:

```json
{
  "hooks": {
    "enabled": true,
    "modules": [".claude/hooks/my_hooks.py"]
  }
}
```

### 3. Verify hooks load

```bash
claude-code --debug
# Look for: [Hooks] Loaded 4 hooks from .claude/hooks/my_hooks.py
```

## Advanced patterns

### Conditional hooks

Only run hooks for specific tools:

```python
def pre_tool_hook(tool_name, args, context):
    if tool_name not in ["Bash", "Edit"]:
        return args  # Skip hook for other tools

    # Custom logic for Bash/Edit only
    validate_args(args)
    return args
```

### Stateful hooks

Maintain state across hook invocations:

```python
# .claude/hooks/telemetry.py
tool_call_count = {}

def pre_tool_hook(tool_name, args, context):
    tool_call_count[tool_name] = tool_call_count.get(tool_name, 0) + 1
    return args

def response_hook(response, context):
    print(f"Tool usage: {tool_call_count}")
```

### Async hooks

Hooks can be async (for I/O-heavy operations):

```python
import asyncio

async def post_tool_hook(tool_name, result, context):
    if tool_name == "Edit":
        await send_webhook({"file": result["file_path"]})
```

### Multiple hook modules

Load multiple hook files:

```json
{
  "hooks": {
    "modules": [
      ".claude/hooks/telemetry.py",
      ".claude/hooks/validation.py",
      ".claude/hooks/auto_commit.py"
    ]
  }
}
```

Hooks run in order—first module's hooks run first.

## Real-world examples

### Example 1: Enforce TDD

Block code edits unless tests exist:

```python
def pre_tool_hook(tool_name, args, context):
    if tool_name == "Edit":
        file_path = args["file_path"]
        if file_path.endswith(".py") and not file_path.startswith("test_"):
            test_file = f"test_{file_path}"
            if not os.path.exists(test_file):
                raise ValueError(f"Write tests first: {test_file} missing")
    return args
```

### Example 2: Track tool performance

Log execution time for all tools:

```python
import time

start_times = {}

def pre_tool_hook(tool_name, args, context):
    start_times[tool_name] = time.time()
    return args

def post_tool_hook(tool_name, result, context):
    duration = time.time() - start_times.get(tool_name, 0)
    with open(".claude/perf.log", "a") as f:
        f.write(f"{tool_name},{duration:.3f}s\n")
```

### Example 3: Auto-format on edit

Run `black` after every file edit:

```python
import subprocess

def post_tool_hook(tool_name, result, context):
    if tool_name == "Edit":
        file_path = result["file_path"]
        if file_path.endswith(".py"):
            subprocess.run(["black", file_path])
```

### Example 4: Block destructive git operations

Prevent force pushes and hard resets:

```python
def pre_tool_hook(tool_name, args, context):
    if tool_name == "Bash":
        cmd = args.get("command", "")
        if "git push --force" in cmd or "git reset --hard" in cmd:
            raise ValueError("Destructive git operation blocked")
    return args
```

## Best practices

### 1. Keep hooks fast

Hooks run synchronously—slow hooks block tool execution. For heavy operations, use async or background tasks.

### 2. Handle errors gracefully

Don't let hook failures crash Claude Code:

```python
def post_tool_hook(tool_name, result, context):
    try:
        send_telemetry(tool_name, result)
    except Exception as e:
        print(f"Hook error (non-fatal): {e}")
```

### 3. Log hook activity

Use `--debug` to see hook execution:

```bash
claude-code --debug
# [Hooks] pre_tool_hook(Bash) -> args modified
# [Hooks] post_tool_hook(Bash) -> completed
```

### 4. Avoid modifying tool results

Post-tool hooks receive `result` but shouldn't mutate it (read-only). Use side effects instead.

### 5. Test hooks independently

Write unit tests for hook logic:

```python
# test_hooks.py
from .claude.hooks.my_hooks import pre_tool_hook

def test_blocks_dangerous_commands():
    with pytest.raises(ValueError):
        pre_tool_hook("Bash", {"command": "rm -rf /"}, {})
```

## Debugging hooks

### Enable debug logging

```bash
claude-code --debug
```

### Print hook context

```python
def pre_tool_hook(tool_name, args, context):
    print(f"Context: {json.dumps(context, indent=2)}")
    return args
```

### Disable specific hooks

Comment out functions to isolate issues:

```python
# def pre_tool_hook(tool_name, args, context):
#     # Temporarily disabled
#     return args
```

## Limitations

- **Sync execution**: Hooks block tool execution (use async for I/O).
- **No response modification**: Response hooks can't change Claude's output.
- **Error handling**: Exceptions in hooks propagate—handle them or Claude Code will abort.
- **State persistence**: Hook state is in-memory (use files/db for persistence).

## FAQ

**Q: Can hooks modify Claude's responses?**
A: No. Response hooks are read-only (for logging/analysis). Tool results can't be modified either.

**Q: Do hooks work in headless mode?**
A: Yes. Hooks run in all modes (CLI, headless, server).

**Q: Can I disable hooks temporarily?**
A: Set `"enabled": false` in `.claude/config.json` or use `--no-hooks` flag.

**Q: How do I share hooks across projects?**
A: Symlink `.claude/hooks/` or copy hook files to each project's `.claude/` directory.

**Q: Can hooks call tools?**
A: Yes, but be careful—avoid infinite loops (e.g., a pre-tool hook that triggers another tool).

---

**Next steps:**

- Create a simple telemetry hook to log tool usage.
- Build a validation hook to enforce your project's coding standards.
- Explore async hooks for non-blocking side effects.
