#!/usr/bin/env python3
"""
Debug Tool Integration Test
Direct test to see if agent can actually use tools
"""

import asyncio
from dotenv import load_dotenv
from claude_code_agent import claude_code_agent
from agency_swarm import Agency

# Load environment variables
load_dotenv()

# Create agency with detailed settings
agency = Agency(
    claude_code_agent,
    communication_flows=[],
    shared_instructions="You MUST use the available tools to complete tasks. When asked to list files, use the LS tool. When asked to read files, use the Read tool. When asked to search files, use the Grep tool. Always execute the appropriate tools rather than providing instructions.",
)

async def test_tool_usage():
    """Test specific tool usage scenarios"""
    
    print("=" * 60)
    print("DEBUG: TOOL INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Simple LS command
    print("\n=== Test 1: Direct LS Tool Usage ===")
    print("Query: Use the LS tool to list files in the current directory")
    
    try:
        result = await agency.get_response("Use the LS tool to list files in the current directory")
        print(f"Response Type: {type(result)}")
        print(f"Response: {result}")
        
        # Check if tools were actually used
        if hasattr(result, 'text'):
            response_text = result.text
            print(f"Text content: {response_text}")
            
            # Check for tool usage indicators
            if "LS" in response_text or "files" in response_text.lower():
                print("✅ Tool usage detected")
            else:
                print("❌ No tool usage detected")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 2: Direct tool instruction
    print("\n=== Test 2: Explicit Tool Instruction ===")
    print("Query: Execute the LS tool with path parameter set to '.'")
    
    try:
        result = await agency.get_response("Execute the LS tool with path parameter set to '.' to show me the files")
        print(f"Response: {result}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 3: Check available tools
    print("\n=== Test 3: Agent Tool Inspection ===")
    print("Available tools:")
    if hasattr(claude_code_agent, 'tools'):
        for tool in claude_code_agent.tools:
            print(f"- {tool}")
    else:
        print("No tools attribute found")
    
    # Test 4: Manual tool verification
    print("\n=== Test 4: Manual Tool Import Test ===")
    try:
        from tools.ls import LS
        ls_tool = LS()
        print("✅ LS tool imported successfully")
        # Test the tool directly
        ls_result = ls_tool.run(path="/Users/vrsen/Areas/Development/code/agency-swarm/claude_code")
        print(f"Direct LS result: {ls_result}")
    except Exception as e:
        print(f"❌ LS tool import failed: {e}")
        
    # Test 5: Check tools folder contents
    print("\n=== Test 5: Tools Folder Analysis ===")
    import os
    tools_path = "/Users/vrsen/Areas/Development/code/agency-swarm/claude_code/tools"
    if os.path.exists(tools_path):
        tool_files = [f for f in os.listdir(tools_path) if f.endswith('.py') and f != '__init__.py']
        print(f"Tool files found: {tool_files}")
        
        # Try to import each tool
        for tool_file in tool_files[:3]:  # Test first 3 tools
            tool_name = tool_file[:-3]  # Remove .py
            try:
                module = __import__(f'tools.{tool_name}', fromlist=[''])
                # Get all classes from module
                classes = [cls for cls in dir(module) if not cls.startswith('_')]
                print(f"✅ {tool_file}: classes = {classes}")
            except Exception as e:
                print(f"❌ {tool_file}: import error = {e}")
    
    # Test 6: Better query with explicit tool usage
    print("\n=== Test 6: Force Tool Usage ===")
    print("Query: I need you to run the LS tool right now to show all files")
    
    try:
        result = await agency.get_response("I need you to run the LS tool right now to show all files in /Users/vrsen/Areas/Development/code/agency-swarm/claude_code directory")
        print(f"Response: {result}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_tool_usage())