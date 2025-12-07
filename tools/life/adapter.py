"""
Life Tool Adapter
=================

Adapts "Life Tools" (Steve Jobs style) to "Lean Agent Tools" (OpenAI style).
Allows LifeTools (and SafetyGuards) to be used by the LeanAgent.
"""

import json
from typing import List, Any
from shared.lean_agent import Tool, ToolParameter, ToolPropertySchema
from tools.life.base import LifeTool
from shared.safety_guard import SafetyGuard

class LifeToolAdapter:
    @staticmethod
    def to_tool(life_tool: LifeTool | SafetyGuard) -> Tool:
        """
        Convert a LifeTool (or SafetyGuard) into a LeanAgent Tool.
        
        The resulting Tool will have:
        - name: The name of the LifeTool
        - description: The description + capabilities
        - parameters: 'action' (enum) and 'data' (JSON string)
        - function: A wrapper around life_tool.execute()
        """
        # Get the underlying tool for metadata
        real_tool = life_tool.tool if isinstance(life_tool, SafetyGuard) else life_tool
        
        capabilities = real_tool.get_capabilities()
        
        # Define the function that the agent will call
        def execute_wrapper(action: str, data: str = "{}"):
            try:
                kwargs = json.loads(data)
            except json.JSONDecodeError:
                return f"Error: 'data' must be valid JSON. You provided: {data}"
            except Exception as e:
                return f"Error parsing arguments: {e}"
                
            try:
                result = life_tool.execute(action, **kwargs)
                if result.success:
                    return result.message + (f"\nData: {result.data}" if result.data else "")
                else:
                    return f"Error: {result.error} - {result.message}"
            except Exception as e:
                return f"Execution Error: {str(e)}"

        # Define parameters
        params = ToolParameter(
            type="object",
            properties={
                "action": ToolPropertySchema(
                    type="string",
                    description=f"Action to perform. Options: {', '.join(capabilities)}",
                    enum=capabilities
                ),
                "data": ToolPropertySchema(
                    type="string",
                    description="JSON string of arguments for the action. e.g. '{\"title\": \"Meeting\", \"time\": \"tomorrow\"}'"
                )
            },
            required=["action"]
        )

        return Tool(
            name=real_tool.name,
            description=real_tool.description + f" Capabilities: {', '.join(capabilities)}",
            parameters=params,
            function=execute_wrapper
        )
