import importlib
import inspect
import os
import sys
from pathlib import Path
from typing import List, Callable, Dict, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[2]))

from cells.shared.lean_agent import tool, ToolParameter, ToolPropertySchema

class ToolRegistry:
    """
    Dynamically discovers and registers tools from the 'tools/' directory.
    Allows the ActionCell to access the full capabilities of the AgencyOS.
    """
    
    def __init__(self, tools_dir: str = "tools"):
        self.tools_dir = Path(tools_dir)
        self.registered_tools: List[Callable] = []
        self._tool_cache: Dict[str, Callable] = {}

    def scan_and_register(self) -> List[Callable]:
        """
        Scans the tools directory for python modules and extracts valid tools.
        Returns the list of found tool functions.
        """
        print(f"🔍 Registry: Scanning {self.tools_dir} for tools...")
        
        if not self.tools_dir.exists():
            print(f"⚠️ Registry: Directory {self.tools_dir} not found.")
            return []

        # 1. Walk through the directory
        for file_path in self.tools_dir.rglob("*.py"):
            # Skip unwanted files
            if file_path.name.startswith("_") or "test" in file_path.name or "voice_v2" in file_path.parts or "demo" in file_path.name:
                # print(f"Skipping {file_path}")
                continue
                
            tool_func = self._load_tool_from_file(file_path)
            if tool_func:
                print(f"   -> Found potential tool in {file_path.name}")
                self.register(tool_func)

        print(f"✅ Registry: Loaded {len(self.registered_tools)} tools.")
        return self.registered_tools

    def register(self, tool_obj: Any):
        """Manually register a tool function or Tool object."""
        # Check if it's already a Tool object (from lean_agent.tool decorator)
        if hasattr(tool_obj, "name") and hasattr(tool_obj, "function"):
             name = tool_obj.name
             if name not in self._tool_cache:
                self.registered_tools.append(tool_obj)
                self._tool_cache[name] = tool_obj
                print(f"   - Registered: {name}")
             return

        # Legacy check: does it have a __tool_name__ attribute? (Custom decorators)
        if hasattr(tool_obj, "__tool_name__") or hasattr(tool_obj, "tool_schema"):
            # Avoid duplicates
            name = getattr(tool_obj, "__tool_name__", tool_obj.__name__)
            if name not in self._tool_cache:
                self.registered_tools.append(tool_obj)
                self._tool_cache[name] = tool_obj
                print(f"   - Registered: {name}")

    def _load_tool_from_file(self, file_path: Path) -> Optional[Callable]:
        """Attempt to load a 'main' entry point or @tool decorated functions from a file."""
        try:
            # Construct module name from path
            # e.g. tools/voice/listener.py -> tools.voice.listener
            abs_path = file_path.resolve()
            try:
                relative_path = abs_path.relative_to(Path.cwd())
            except ValueError:
                # If file is not in CWD (symlinks etc), skip import or try name only
                relative_path = file_path
            
            module_name = str(relative_path).replace(os.sep, ".").replace(".py", "")
            
            # Helper to reload if already imported (for hot updates)
            if module_name in sys.modules:
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)
            
            # Strategy 1: Smart Scraper - Look for @tool decorated functions OR Tool objects
            found_tools = []
            for name, obj in inspect.getmembers(module):
                # Check for legacy functions
                if inspect.isfunction(obj) and hasattr(obj, "__tool_name__"):
                    found_tools.append(obj)
                # Check for new Tool objects (from lean_agent.tool)
                elif hasattr(obj, "name") and hasattr(obj, "function") and hasattr(obj, "description"):
                     # It's a Tool object!
                     found_tools.append(obj)
            
            if found_tools:
                return found_tools[0] 

            # Strategy 2: "Main" Wrapper
            tool_name = f"run_{file_path.stem}"
            
            # Only wrap if it looks like a script (has "main", "run", or uses entry point check)
            # Heuristic: Read file content to check for "__main__"
            content = file_path.read_text()
            is_script = hasattr(module, "main") or hasattr(module, "run") or 'if __name__ == "__main__":' in content
            
            if is_script:
                return self._create_script_wrapper(file_path, tool_name)
                
        except Exception as e:
            # print(f"   ⚠️ Registry Warning: Failed to load {file_path.name}: {e}")
            # Fallback: If we can't import it, but it looks like a script, valid it anyway
            try:
                content = file_path.read_text()
                tool_name = f"run_{file_path.stem}"
                # Relaxed: check for __main__ anywhere (e.g. if __name__ == '__main__': or if __name__=="__main__":)
                if '__main__' in content:
                     # print(f"   Wrapper: Creating raw script wrapper for {file_path.name}")
                     return self._create_script_wrapper(file_path, tool_name)
            except:
                pass
            pass
            
        return None

    def _create_script_wrapper(self, file_path: Path, tool_name: str) -> Callable:
        """Creates a tool wrapper around a python script."""
        
        @tool(
            name=tool_name,
            description=f"Executes the {file_path.name} script. Use this to run this specific capability.",
            parameters=ToolParameter(
                type="object",
                properties={
                    "arguments": ToolPropertySchema(
                        type="string", 
                        description="Command line arguments for the script (e.g. '--limit 10')"
                    )
                },
                required=[]
            )
        )
        def script_wrapper(arguments: str = "") -> str:
            import subprocess
            cmd = f"python3 {file_path} {arguments}"
            print(f"🔧 Registry Running: {cmd}")
            try:
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=300 # 5 min timeout for scripts
                )
                output = result.stdout + "\n" + result.stderr
                return output[-5000:] # Return last 5k chars
            except Exception as e:
                return f"Error running script: {e}"
        
        return script_wrapper

if __name__ == "__main__":
    # Test registry
    registry = ToolRegistry()
    registry.scan_and_register()
