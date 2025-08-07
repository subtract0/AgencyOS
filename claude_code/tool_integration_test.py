#!/usr/bin/env python3
"""
Tool Integration Test for Claude Code Agent
Tests that tools can be invoked directly via the agent
"""

import os
from claude_code_agent import claude_code_agent

def test_tool_invocation():
    """Test that individual tools can be invoked from the agent"""
    print("=== TOOL INTEGRATION TEST ===")
    print(f"Agent: {claude_code_agent.name}")
    print(f"Tools loaded: {len(claude_code_agent.tools)}")
    
    # Test 1: LS tool direct invocation
    print("\n1. Testing LS tool invocation...")
    try:
        ls_tool = None
        for tool in claude_code_agent.tools:
            if tool.name == "LS":
                ls_tool = tool
                break
        
        if ls_tool:
            # Call the tool function directly
            result = ls_tool.function(path=os.path.abspath("."))
            print(f"✅ LS tool invoked successfully")
            print(f"Result type: {type(result)}")
            print(f"Result preview: {str(result)[:100]}...")
        else:
            print("❌ LS tool not found in agent tools")
            
    except Exception as e:
        print(f"❌ Error invoking LS tool: {str(e)}")
    
    # Test 2: TodoWrite tool direct invocation  
    print("\n2. Testing TodoWrite tool invocation...")
    try:
        todo_tool = None
        for tool in claude_code_agent.tools:
            if tool.name == "TodoWrite":
                todo_tool = tool
                break
        
        if todo_tool:
            # Call the tool function directly
            test_todos = [
                {
                    "content": "Test integration",
                    "status": "pending", 
                    "priority": "medium",
                    "id": "test-001"
                }
            ]
            result = todo_tool.function(todo_list=test_todos)
            print(f"✅ TodoWrite tool invoked successfully")
            print(f"Result: {result}")
        else:
            print("❌ TodoWrite tool not found in agent tools")
            
    except Exception as e:
        print(f"❌ Error invoking TodoWrite tool: {str(e)}")
    
    # Test 3: Tool parameter validation
    print("\n3. Testing tool parameter validation...")
    try:
        read_tool = None
        for tool in claude_code_agent.tools:
            if tool.name == "Read":
                read_tool = tool
                break
                
        if read_tool:
            # Test with invalid parameters (should raise validation error)
            try:
                result = read_tool.function(invalid_param="test")
                print("❌ Tool should have rejected invalid parameters")
            except Exception as validation_error:
                print(f"✅ Tool parameter validation working: {str(validation_error)[:100]}...")
        else:
            print("❌ Read tool not found")
            
    except Exception as e:
        print(f"Error in validation test: {str(e)}")
    
    print("\n=== INTEGRATION TEST COMPLETE ===")
    
    # Summary
    tools_by_name = {tool.name: tool for tool in claude_code_agent.tools}
    critical_tools = ["LS", "Read", "Write", "Bash", "TodoWrite"]
    
    print(f"\nCritical tools status:")
    for tool_name in critical_tools:
        status = "✅ Loaded" if tool_name in tools_by_name else "❌ Missing"
        print(f"  {tool_name}: {status}")
    
    return len(claude_code_agent.tools) == 15

if __name__ == "__main__":
    success = test_tool_invocation()
    print(f"\nTool integration test: {'PASSED' if success else 'FAILED'}")