import sys
import os
import json
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[2]))

from cells.shared.lean_agent import LeanAgent, AgentConfig, tool, ToolParameter, ToolPropertySchema
from cells.governor.budget import BudgetManager
from cells.shared.model_profiles import MODELS
import subprocess
import requests # For Dashboard Communication
from agency_memory.pattern_memory import get_pattern_memory, Pattern
from cells.maintenance.supervisor import run_maintenance_cycle_tool
from cells.shared.message_bus import MessageBus, async_message_bus
from cells.action.speak_tool import speak

DASHBOARD_URL = "http://127.0.0.1:8000/api/status"

def send_dashboard_update(endpoint: str, data: dict):
    """Fire and forget update to Visual Cortex."""
    try:
        requests.post(f"{DASHBOARD_URL}/{endpoint}", json=data, timeout=0.1)
    except:
        pass # Don't block action if dashboard is down

# Define Tools
@tool(
    name="run_shell",
    description="Execute a shell command. Use this to run tests, list files, etc.",
    parameters=ToolParameter(
        type="object",
        properties={
            "command": ToolPropertySchema(type="string", description="The shell command to run")
        },
        required=["command"]
    )
)
def run_shell(command: str) -> str:
    print(f"🔧 Running: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=120
        )
        output = result.stdout + "\n" + result.stderr
        return output[:5000] # Truncate large output
    except Exception as e:
        return f"Error: {e}"

@tool(
    name="write_file",
    description="Write content to a file. Overwrites if exists.",
    parameters=ToolParameter(
        type="object",
        properties={
            "path": ToolPropertySchema(type="string", description="File path"),
            "content": ToolPropertySchema(type="string", description="File content")
        },
        required=["path", "content"]
    )
)
def write_file(path: str, content: str) -> str:
    print(f"💾 Writing to: {path}")
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return "File written successfully."
    except Exception as e:
        return f"Error writing file: {e}"

@tool(
    name="read_file",
    description="Read content from a file.",
    parameters=ToolParameter(
        type="object",
        properties={
            "path": ToolPropertySchema(type="string", description="File path")
        },
        required=["path"]
    )
)
def read_file(path: str) -> str:
    print(f"📖 Reading: {path}")
    try:
        if not os.path.exists(path):
            return "Error: File not found."
        with open(path, "r") as f:
            return f.read()[:10000] # Truncate
    except Exception as e:
        return f"Error reading file: {e}"

@tool(
    name="take_screenshot",
    description="Capture a screenshot of the current screen state. Call this BEFORE verifying UI.",
    parameters=ToolParameter(
        type="object",
        properties={
            "filename": ToolPropertySchema(type="string", description="Filename to save (e.g. proof.png)")
        },
        required=["filename"]
    )
)
def take_screenshot(filename: str) -> str:
    path = os.path.abspath(filename)
    try:
        # Use macOS native screencapture
        # -x: mute sound
        subprocess.run(["screencapture", "-x", path], check=True)
        
        # Push to Dashboard (The Eye)
        # We need to serve this image or encode it. 
        # For MVP: Dashboard reads local file? No, browser sandbox.
        # We'll base64 encode it for the dashboard (MVP style).
        import base64
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
            send_dashboard_update("eye", {
                "state": "Observing", 
                "image_url": f"data:image/png;base64,{b64}"
            })

        return f"Screenshot saved to {path}"
    except Exception as e:
        return f"Failed to take screenshot: {e}"

@tool(
    name="verify_with_vision",
    description="Ask 'The Eye' (VLM) to verify a screenshot. Must take screenshot first.",
    parameters=ToolParameter(
        type="object",
        properties={
            "image_path": ToolPropertySchema(type="string"),
            "question": ToolPropertySchema(type="string", description="What should 'The Eye' check?")
        },
        required=["image_path", "question"]
    )
)
def verify_with_vision(image_path: str, question: str) -> str:
    """Send image to Qwen2.5-VL (The Eye) for verification."""
    print(f"👁️ Asking The Eye: {question}")
    import base64
    import requests
    
    # 1. Load Profile
    profile = MODELS["qwen_vl"]
    
    # 2. Encode Image
    try:
        if not os.path.exists(image_path):
            return "Error: Image file not found."
            
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        return f"Error reading image: {e}"

    # 3. Call VLM API
    payload = {
        "model": profile.name,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_string}"}}
                ]
            }
        ],
        "max_tokens": 500
    }
    
    try:
        response = requests.post(f"{profile.api_base}/chat/completions", json=payload)
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            return f"👁️ THE EYE SAYS: {content}"
        else:
            return f"Error from VLM: {response.text}"
    except Exception as e:
        return f"Failed to connect to VLM ({profile.api_base}): {e}"


@tool(
    name="talk",
    description="Reply to the user. Use this for greetings, questions, or summarizing results.",
    parameters=ToolParameter(
        type="object",
        properties={
            "message": ToolPropertySchema(type="string", description="The response text")
        },
        required=["message"]
    )
)
def talk(message: str) -> str:
    """Return the message to be displayed in the dashboard as a System Log."""
    # The dashboard picks up logs. We return it so the agent sees it delivered.
    return f"🗣️ Replied: {message}"

@tool(
    name="audit_codebase",
    description="Run a full audit of the codebase (Structure, Size, TODOs). Use this when asked to 'audit' or 'overview' the system.",
    parameters=ToolParameter(
        type="object",
        properties={},
        required=[]
    )
)
def audit_codebase() -> str:
    return subprocess.run(["./skills/audit.sh"], capture_output=True, text=True).stdout

@tool(
    name="consult_memory",
    description="Search core memory for similar patterns or solutions. Use this BEFORE starting a complex task.",
    parameters=ToolParameter(
        type="object",
        properties={
            "query": ToolPropertySchema(type="string", description="The problem or topic to search for"),
            "tags": ToolPropertySchema(type="array", items={"type": "string"}, description="Optional tags to filter by")
        },
        required=["query"]
    )
)
def consult_memory(query: str, tags: list[str] = []) -> str:
    print(f"🧠 Consulting Memory: {query} (Tags: {tags})")
    send_dashboard_update("hand", {"state": "Remembering", "log": f"Recalling: {query}"})
    
    try:
        mem = get_pattern_memory()
        
        if not tags:
            return "Please provide at least one relevant tag using the 'tags' argument (e.g. ['python', 'error', 'deploy'])"
            
        patterns = mem.query(tags, limit=5)
        
        if not patterns:
            return "No relevant memories found."
            
        results = []
        for p in patterns:
            results.append(f"--- Pattern {p.id} (Confidence: {p.confidence:.2f}) ---\nTags: {p.tags}\nContent: {p.content}")
            
        return "\n\n".join(results)
    except Exception as e:
        return f"Error accessing memory: {e}"

@tool(
    name="save_pattern",
    description="Save a useful solution, insight, or pattern to long-term memory.",
    parameters=ToolParameter(
        type="object",
        properties={
            "title": ToolPropertySchema(type="string", description="Short title for the pattern"),
            "problem": ToolPropertySchema(type="string", description="The problem or context"),
            "solution": ToolPropertySchema(type="string", description="The solution or insight"),
            "tags": ToolPropertySchema(type="array", items={"type": "string"}, description="Tags for retrieval")
        },
        required=["title", "problem", "solution", "tags"]
    )
)
def save_pattern(title: str, problem: str, solution: str, tags: list[str]) -> str:
    print(f"💾 Saving Pattern: {title}")
    try:
        mem = get_pattern_memory()
        
        # Create meaningful ID
        import uuid
        pattern_id = f"pat_{uuid.uuid4().hex[:8]}"
        
        pattern = Pattern(
            id=pattern_id,
            content={
                "title": title,
                "problem": problem,
                "solution": solution
            },
            tags=tags,
            confidence=0.9 # High confidence for explicit saves
        )
        
        mem.store(pattern)
        return f"Pattern saved as {pattern_id}."
    except Exception as e:
        return f"Error saving pattern: {e}"

@tool(
    name="spawn_agent",
    description="Spawn a new autonomous background agent (Class 17 Hive).",
    parameters=ToolParameter(
        type="object",
        properties={
            "name": ToolPropertySchema(type="string", description="Name of the agent (e.g. 'CryptoWatcher')"),
            "instructions": ToolPropertySchema(type="string", description="System instructions/role"),
            "tools": ToolPropertySchema(type="array", description="List of tool names to give the agent"),
            "schedule": ToolPropertySchema(type="string", description="Optional: Schedule (cron or 'loop_60s'). Default is 60s loop.")
        },
        required=["name", "instructions"]
    )
)
def spawn_agent(name: str, instructions: str, tools: list[str] = [], schedule: str = None) -> str:
    from cells.manager.process_manager import get_process_manager
    
    print(f"🐝 Spawning Agent: {name}")
    manager = get_process_manager()
    
    # Construct Manifest
    manifest = {
        "name": name,
        "instructions": instructions,
        "tools": tools,
        "model": "gpt-4o", # Default for now
        "loop_interval_seconds": 60 # Default
    }
    
    try:
        agent_id = manager.spawn_agent(manifest)
        
        # Publish Event to Bus
        async def _notify():
            async with async_message_bus() as bus:
                await bus.publish("hive", {
                    "event": "spawn",
                    "agent_id": agent_id,
                    "name": name
                })
        # We are in a sync function, so we need to run async code appropriately.
        # ActionCell isn't fully async context yet, but tools are synchronous (mostly).
        # We can use requests to bridge or just fire-and-forget via a helper?
        # Or better: MessageBus is persistent SQLite. We can just open a connection and publish synchronously if we had a sync wrapper.
        # But MessageBus is async.
        # Hack for MVP: import asyncio and run.
        import asyncio
        try:
             asyncio.run(_notify())
        except Exception as e:
             print(f"Bus Error: {e}")
             
        return f"Successfully spawned agent '{name}' (ID: {agent_id}). It is now running in the background."
    except Exception as e:
        return f"Failed to spawn agent: {e}"
@tool(
    name="link_patterns",
    description="Create a semantic link between two memory patterns (e.g. 'Fix A' causes 'Bug B' or 'Concept X' relates to 'Concept Y').",
    parameters=ToolParameter(
        type="object",
        properties={
            "source_id": ToolPropertySchema(type="string", description="ID of the source pattern or concept"),
            "target_id": ToolPropertySchema(type="string", description="ID of the target pattern or concept"),
            "relation": ToolPropertySchema(type="string", description="Relationship type: 'fixes', 'relates_to', 'caused_by'")
        },
        required=["source_id", "target_id", "relation"]
    )
)
def link_patterns(source_id: str, target_id: str, relation: str = "relates_to") -> str:
    print(f"🔗 Linking: {source_id} --[{relation}]--> {target_id}")
    try:
        from agency_memory.knowledge_graph import EdgeType
        mem = get_pattern_memory()
        
        # Validate relation
        try:
            edge_type = EdgeType(relation.lower())
        except ValueError:
            return f"Invalid relation '{relation}'. Valid types: {[t.value for t in EdgeType]}"
        
        mem.graph.add_edge(source_id, target_id, edge_type)
        mem.graph.save()
        
        return f"Link created: {source_id} -> {relation} -> {target_id}"
    except Exception as e:
        return f"Error linking patterns: {e}"

class ActionCell:
    """
    The 'Hand' of the organism.
    A unified Deep Thinking Cell that plans, codes, and verifies.
    Now equipped with 'The Eye' (Qwen-VL) for visual verification.
    """
    
    def __init__(self):
        self.budget = BudgetManager()
        
        # Configure Environment for Local MLX via Profile
        # We use the Nemotron profile for the Action Cell (Fast Brain)
        profile = MODELS["nemotron"]
        
        os.environ["OPENAI_API_KEY"] = profile.api_key
        os.environ["OPENAI_API_BASE"] = profile.api_base
        
        # Configure Agent
        config = AgentConfig(
            name="ActionCell",
            instructions="""
            YOU ARE THE ACTION CELL. You are the interface between the User and the Codebase.
            
            PROTOCOL:
            1. ANALYZE: Is the user input a TASK (Do something) or a CONVERSATION (Say something)?
            
            IF CONVERSATION (Greetings, Questions about you):
               - Use `talk` to reply locally.
               - DONE.
            
            IF TASK (Refactor, Audit, Build, Fix):
               - PLAN: Think.
               - EXECUTE: Use `write_file`, `run_shell`, or `audit_codebase`.
               - VERIFY: Use `verify_with_vision` if UI.
               - REPORT: Use `talk` to summarize what you did.
               - DONE.
            """,
            model=profile.name,
            max_tokens=profile.max_tokens,
            tools=[
                run_shell,
                write_file,
                read_file,
                take_screenshot,
                verify_with_vision,
                talk,
                talk,
                audit_codebase,
                consult_memory,
                save_pattern,
                link_patterns,
                run_maintenance_cycle_tool,
                spawn_agent,
                speak
            ],
            max_iterations=30
        )
        
        # Integrate Tool Registry (Class 4 Upgrade)
        from cells.action.tool_registry import ToolRegistry
        self.registry = ToolRegistry()
        discovered_tools = self.registry.scan_and_register()
        
        # Extend agent tools with discovered ones
        config.tools.extend(discovered_tools)
        
        print(f"🧬 Action Cell: Evolved with {len(discovered_tools)} external tools.")
        
        self.agent = LeanAgent(config)
        self.memory_path = Path(".agency/cells/action_memory.json")
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)

    def process_signal(self, signal: str):
        """
        Takes a raw signal (e.g. 'Build landing page for X') and executes it.
        """
        print(f"🔴 Action Cell: Processing signal: {signal}")
        send_dashboard_update("hand", {"state": "Thinking", "log": f"Processing: {signal}"})
        
        # 1. Check Governor
        if not self.budget.check_budget(0.0): # Zero cost for local, but check safety
            print("🛑 Governor: Budget exceeded. Action halted.")
            send_dashboard_update("hand", {"state": "Halted", "log": "Budget Exceeded"})
            return

        # 2. Think & Act (The Loop)
        prompt = f"OBJECTIVE: {signal}\n\nExecute."
        
        try:
            send_dashboard_update("hand", {"state": "Working", "log": "Engaging Agent Loop..."})
            result = self.agent.run(prompt)
            print(f"✅ Action Cell: Complete. Result: {result}")
            send_dashboard_update("hand", {"state": "Idle", "log": f"Task Complete: {result}"})
        except Exception as e:
            print(f"❌ Action Cell: Failed. Error: {e}")
            send_dashboard_update("hand", {"state": "Error", "log": str(e)})

if __name__ == "__main__":
    # Test execution
    if len(sys.argv) > 1:
        signal = sys.argv[1]
        cell = ActionCell()
        cell.process_signal(signal)
    else:
        print("Usage: python action_cell.py 'Task description'")
