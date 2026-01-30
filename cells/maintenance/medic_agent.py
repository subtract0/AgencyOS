
import os
from typing import Optional

from cells.shared.lean_agent import AgentConfig, LeanAgent, tool, ToolParameter, ToolPropertySchema
from cells.action.tool_registry import ToolRegistry

# Define specialized tools for the Medic

@tool("run_tests", "Run the test suite or specific tests", ToolParameter(
    type="object",
    properties={
        "test_path": ToolPropertySchema(type="string", description="Path to specific test file or directory"),
        "fast": ToolPropertySchema(type="boolean", description="Run only fast tests"),
    }
))
def run_tests_tool(test_path: Optional[str] = None, fast: bool = True) -> str:
    """Run tests using the project's run_tests.py."""
    cmd = ["python", "run_tests.py"]
    if fast:
        cmd.append("--fast")
    if test_path:
        cmd.append(test_path)
    
    # We use a subprocess here to run the command
    import subprocess
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        output = f"Exit Code: {result.returncode}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        if result.returncode == 0:
            return "✅ Tests Passed.\n" + output
        else:
            return "❌ Tests Failed.\n" + output
    except subprocess.TimeoutExpired:
        return "❌ Tests Timed Out."
    except Exception as e:
        return f"❌ Error running tests: {str(e)}"

def create_medic_agent(model: str = "gpt-4o") -> LeanAgent:
    """Create the Medic Agent."""
    
    # ... (instructions omitted for brevity in thought, but I must keep them if I replace the whole function, or just the import/usage)
    # I'll replace the import first, then the usage.
    # Actually, I'll allow replace_file_content to do it.

    instructions = """
    You are the **Medic**, the AgencyOS Self-Healing Unit.
    Your mission is to maintain the health of the codebase.

    **Protocol:**
    1.  **Diagnose**: Run tests using `run_tests` tool.
    2.  **Analyze**: Read test failure output and identify the root cause.
    3.  **Treat**: specifics files using `read_file` and `write_file` / `replace` to fix bugs.
    4.  **Verify**: Re-run the tests to confirm the fix.

    **Guidelines:**
    - Start with `run_tests(fast=True)`.
    - If a specific test fails, focus on that file.
    - Do not attempt sweeping refactors. Fix the bug only.
    - If `fast` tests pass, you are healthy.
    """

    config = AgentConfig(
        name="Medic",
        instructions=instructions,
        model=model,
        tools=[run_tests_tool]
    )
    
    agent = LeanAgent(config)
    
    # Register standard OS tools (read, write, etc)
    registry_instance = ToolRegistry()
    registry_tools = registry_instance.scan_and_register()
    
    # We specifically want: read, write, grep, ls
    desired_tools = ["read", "write", "grep", "ls"]
    
    for t in registry_tools:
         # Rough matching by name
         if any(desired in t.name for desired in desired_tools):
             agent.register_tools(t)
             
    return agent

if __name__ == "__main__":
    # Self-test
    medic = create_medic_agent()
    print("Medic Agent initialized.")
    # result = medic.run("Run sanity check on tests/test_lean_agent.py")
    # print(result)
