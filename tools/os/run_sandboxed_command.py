from cells.shared.lean_agent import tool, ToolParameter, ToolPropertySchema
import subprocess
import os
import sys

# Tool Definition
SCHEMA = ToolParameter(
    type="object",
    properties={
        "command": ToolPropertySchema(type="string", description="The command to execute inside the sandbox."),
        "image": ToolPropertySchema(type="string", description="Docker image to use (default: python:3.12-slim)."),
        "timeout": ToolPropertySchema(type="number", description="Timeout in seconds (default 30)."),
    },
    required=["command"]
)

@tool("run_sandboxed_command", "Execute a command safely using a Docker container. Use this for untrusted code or filesystem operations that should not affect the host.", SCHEMA)
def run_sandboxed_command(command: str, image: str = "python:3.12-slim", timeout: float = 30.0) -> str:
    """
    Executes a command inside a transient Docker container.
    Mounts the current directory to /app and sets it as working directory.
    """
    cwd = os.getcwd()
    
    # Construct Docker command
    # --rm: Remove container after exit
    # -v: Mount current directory
    # -w: Set working directory
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{cwd}:/app",
        "-w", "/app",
        image,
        "/bin/sh", "-c", command
    ]
    
    try:
        # Check if docker is running first
        subprocess.run(["docker", "info"], check=True, capture_output=True)
        
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
            
        if result.returncode != 0:
            output += f"\nExit Code: {result.returncode}"
            
        return output
        
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds."
    except subprocess.CalledProcessError:
        return "Error: Docker daemon is not running or not installed."
    except Exception as e:
        return f"Error executing sandboxed command: {e}"

if __name__ == "__main__":
    # Test
    # This will list files in the container's /app (which matches host cwd)
    print(run_sandboxed_command.function("ls -la"))
