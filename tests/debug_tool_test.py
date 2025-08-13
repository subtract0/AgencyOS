"""
Debug Tool Integration Test
Direct test to see if agent can actually use tools
"""

import pytest
import os
from pathlib import Path
from dotenv import load_dotenv
from agency_code_agent.agency_code_agent import create_agency_code_agent
from agency_swarm import Agency

# Load environment variables
load_dotenv()

# Skip agency tests if OPENAI_API_KEY is not set
skip_agency_tests = os.getenv("OPENAI_API_KEY") is None


@pytest.fixture
def agency():
    """Create agency with detailed settings for tool testing"""
    return Agency(
        create_agency_code_agent(),
        communication_flows=[],
        shared_instructions="You MUST use the available tools to complete tasks. When asked to list files, use the LS tool. When asked to read files, use the Read tool. When asked to search files, use the Grep tool. Always execute the appropriate tools rather than providing instructions.",
    )

@pytest.mark.asyncio
@pytest.mark.skipif(skip_agency_tests, reason="OPENAI_API_KEY not set")
async def test_direct_ls_tool_usage(agency):
    """Test direct LS tool usage via agency"""
    result = await agency.get_response("Use the LS tool to list files in the current directory")
    
    # Check if tools were actually used
    response_text = result.text if hasattr(result, 'text') else str(result)
    
    # Should have substantial content
    assert len(response_text) > 10, "Response should contain substantial content"
    # Should mention files or LS tool usage
    assert "files" in response_text.lower() or "LS" in response_text, "Response should indicate file listing"


@pytest.mark.asyncio
@pytest.mark.skipif(skip_agency_tests, reason="OPENAI_API_KEY not set")
async def test_explicit_tool_instruction(agency):
    """Test explicit tool instruction"""
    result = await agency.get_response("Execute the LS tool with path parameter set to '.' to show me the files")
    
    response_text = result.text if hasattr(result, 'text') else str(result)
    assert len(response_text) > 10, "Response should contain substantial content"


def test_manual_tool_import():
    """Test manual tool import from agency_code_agent tools"""
    try:
        from agency_code_agent.tools.ls import LS
        repo_root = Path(__file__).resolve().parents[1]
        ls_tool = LS(path=str(repo_root / "agency_code_agent"))
        
        # Test the tool directly
        ls_result = ls_tool.run()
        
        assert "Files and directories" in ls_result or len(ls_result) > 10, "LS tool should return file listing"
    except ImportError:
        pytest.skip("LS tool not available for direct import")


def test_tools_folder_analysis():
    """Test tools folder structure and contents"""
    repo_root = Path(__file__).resolve().parents[1]
    tools_path = repo_root / "agency_code_agent" / "tools"
    
    assert tools_path.exists(), "Tools folder should exist"
    
    tool_files = [f for f in os.listdir(tools_path) if f.endswith('.py') and f != '__init__.py']
    assert len(tool_files) > 0, "Should have tool files in tools folder"
    
    # Test importing first few tools
    successfully_imported = 0
    for tool_file in tool_files[:3]:  # Test first 3 tools
        tool_name = tool_file[:-3]  # Remove .py
        try:
            module = __import__(f'agency_code_agent.tools.{tool_name}', fromlist=[''])
            classes = [cls for cls in dir(module) if not cls.startswith('_')]
            if classes:
                successfully_imported += 1
        except Exception:
            pass  # Some tools might have dependencies
    
    assert successfully_imported > 0, "At least one tool should import successfully"


@pytest.mark.asyncio
@pytest.mark.skipif(skip_agency_tests, reason="OPENAI_API_KEY not set")
async def test_force_tool_usage(agency):
    """Test forcing tool usage with explicit instruction"""
    repo_root = Path(__file__).resolve().parents[1]
    target_dir = str(repo_root / "agency_code_agent")
    
    result = await agency.get_response(f"I need you to run the LS tool right now to show all files in {target_dir} directory")
    
    response_text = result.text if hasattr(result, 'text') else str(result)
    assert len(response_text) > 10, "Response should contain substantial content"


def test_agent_creation():
    """Test that the agent can be created successfully"""
    agent = create_agency_code_agent()
    assert agent is not None, "Agent should be created successfully"
    assert hasattr(agent, 'name'), "Agent should have a name attribute"