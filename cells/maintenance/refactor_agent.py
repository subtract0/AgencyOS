from typing import List, Dict, Any, Optional
from pathlib import Path
from cells.shared.lean_agent import LeanAgent, AgentConfig, ToolParameter, ToolPropertySchema
from cells.action.tool_registry import ToolRegistry

from cells.shared.lean_agent import LeanAgent, AgentConfig, ToolParameter, ToolPropertySchema

# Create a mock ModelProfile-like object for local config
class LocalModelConfig:
    def __init__(self, name="mlx-community/Qwen2.5-Coder-32B-Instruct-4bit", api_base="http://127.0.0.1:8082/v1", api_key="mlx"):
        self.name = name
        self.api_base = api_base
        self.api_key = api_key
        self.model = name # For some access patterns

class RefactorAgent(LeanAgent):
    """
    The Antibody Agent.
    """
    
    def __init__(self):
        model_config = LocalModelConfig()

        system_prompt = (
            "You are the Antibody for AgencyOS. "
            "Your job is to keep the codebase clean, organized, and robust. "
            "You identify 'code smells', 'structural rot', and 'duplicates'."
        )
        
        config = AgentConfig(
            name="RefactorAgent",
            instructions=system_prompt,
            model=model_config,
            max_tokens=4000
        )
        
        super().__init__(config=config)

        
        # Give it the tools it needs to "sense" and "act" on the code
        # We manually register core tools + the registry scanner
        registry = ToolRegistry()
        found_tools = registry.scan_and_register()
        
        # Use new Clean API
        valid_tools = [t for t in found_tools if hasattr(t, "name")]
        self.register_tools(valid_tools)

    def scan(self) -> str:
        """
        Run a health scan of the codebase.
        Returns a summary string.
        """
        prompt = (
            "Please scan the `tools/` directory. "
            "List all files that seem to be 'loose' (not in a subdirectory) "
            "and suggest a logical folder structure for them. "
            "Format your response as a markdown checklist."
        )
        return self.run(prompt)

if __name__ == "__main__":
    # Test Run
    agent = RefactorAgent()
    print("🦠 Antibody Agent Online.")
    print("🔍 Scanning tools/ directory...")
    report = agent.scan()
    print("\n📝 Report:\n")
    print(report)
