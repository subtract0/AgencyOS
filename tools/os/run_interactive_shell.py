from cells.shared.lean_agent import tool, ToolParameter, ToolPropertySchema
from cells.action.interactive_shell import InteractiveShell
import sys

# Tool Definition
SCHEMA = ToolParameter(
    type="object",
    properties={
        "command": ToolPropertySchema(type="string", description="The command to execute in the shell."),
        "timeout": ToolPropertySchema(type="number", description="Timeout in seconds (default 10)."),
    },
    required=["command"]
)

@tool("run_interactive_shell", "Execute a shell command safely using a PTY (pseudo-terminal). Use this for commands that might be interactive or hang (e.g. scripts asking for input), or just as a safer alternative to subprocess.", SCHEMA)
def run_interactive_shell(command: str, timeout: float = 10.0) -> str:
    """
    Executes a command in an interactive zsh shell environment.
    Handles PTY allocation to prevent hangs from interactive prompts.
    """
    shell = InteractiveShell()
    try:
        print(f"DEBUG: Executing command '{command}' with timeout {timeout}", file=sys.stderr)
        output = shell.execute_command(command, timeout_seconds=int(timeout))
        return output
    except Exception as e:
        return f"Error executing command: {e}"
    finally:
        shell.close()

if __name__ == "__main__":
    import sys
    # Test
    print(run_interactive_shell.function("ls -la"))
