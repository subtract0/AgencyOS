"""
Test Agency for Claude Code Agent
Tests the agent with 5 diverse queries to validate functionality
"""

import pytest
import os
from dotenv import load_dotenv
from agency_swarm import Agency
from claude_code.claude_code_agent import create_claude_code_agent
from pathlib import Path

# Load environment variables
load_dotenv()

# Skip agency tests if OPENAI_API_KEY is not set
skip_agency_tests = os.getenv("OPENAI_API_KEY") is None


@pytest.fixture
def agency():
    """Create single-agent agency for testing"""
    return Agency(
        create_claude_code_agent(),
        communication_flows=[],  # Single agent, no communication flows needed
        shared_instructions="Test agency for Claude Code Agent functionality validation.",
    )

@pytest.fixture
def test_queries():
    """Test queries for agency functionality validation"""
    return [
        {
            "id": 1,
            "category": "File Operations",
            "query": "List files in the current directory and read the contents of the first Python file you find",
            "expected": "Should use LS tool and Read tool sequentially"
        },
        {
            "id": 2,
            "category": "Code Search", 
            "query": "Search for any TODO comments in Python files and show me the results with line numbers",
            "expected": "Should use Grep tool with appropriate pattern"
        },
        {
            "id": 3,
            "category": "Complex Task",
            "query": "Help me create a simple Python script that calculates fibonacci numbers and save it to fib.py. Use the TodoWrite tool to track your progress",
            "expected": "Should use TodoWrite, Write tool, and track progress"
        },
        {
            "id": 4,
            "category": "Web Research",
            "query": "Search for information about Agency Swarm framework and fetch content from the official documentation",
            "expected": "Should use WebSearch and WebFetch tools"
        },
        {
            "id": 5,
            "category": "Development Workflow",
            "query": "Show me the git status and create a sample test file, then stage it for commit",
            "expected": "Should use Bash tool for git commands and Write tool for file creation"
        }
    ]


@pytest.mark.asyncio
@pytest.mark.skipif(skip_agency_tests, reason="OPENAI_API_KEY not set")
async def test_file_operations(agency, test_queries):
    """Test file operations functionality"""
    test_case = test_queries[0]
    run_result = await agency.get_response(test_case['query'])
    response = run_result.text if hasattr(run_result, 'text') else str(run_result)
    
    assert len(response) > 50, "Response should be substantial"
    # Check for actual error patterns, not just the word "error"
    error_patterns = ["ERROR:", "Exception:", "Failed:", "Error occurred"]
    has_errors = any(pattern.lower() in response.lower() for pattern in error_patterns)
    assert not has_errors, "Response should not contain actual errors"


@pytest.mark.asyncio
@pytest.mark.skipif(skip_agency_tests, reason="OPENAI_API_KEY not set")
async def test_code_search(agency, test_queries):
    """Test code search functionality"""
    test_case = test_queries[1]
    run_result = await agency.get_response(test_case['query'])
    response = run_result.text if hasattr(run_result, 'text') else str(run_result)
    
    assert len(response) > 50, "Response should be substantial"
    # Check for actual error patterns, not just the word "error"
    error_patterns = ["ERROR:", "Exception:", "Failed:", "Error occurred"]
    has_errors = any(pattern.lower() in response.lower() for pattern in error_patterns)
    assert not has_errors, "Response should not contain actual errors"


@pytest.mark.asyncio
@pytest.mark.skipif(skip_agency_tests, reason="OPENAI_API_KEY not set")
async def test_complex_task(agency, test_queries):
    """Test complex task with todo tracking"""
    test_case = test_queries[2]
    run_result = await agency.get_response(test_case['query'])
    response = run_result.text if hasattr(run_result, 'text') else str(run_result)
    
    assert len(response) > 50, "Response should be substantial"
    # Check for actual error patterns, not just the word "error"
    error_patterns = ["ERROR:", "Exception:", "Failed:", "Error occurred"]
    has_errors = any(pattern.lower() in response.lower() for pattern in error_patterns)
    assert not has_errors, "Response should not contain actual errors"


@pytest.mark.asyncio
@pytest.mark.skipif(skip_agency_tests, reason="OPENAI_API_KEY not set")
async def test_web_research(agency, test_queries):
    """Test web research functionality"""
    test_case = test_queries[3]
    run_result = await agency.get_response(test_case['query'])
    response = run_result.text if hasattr(run_result, 'text') else str(run_result)
    
    assert len(response) > 50, "Response should be substantial"
    # Check for actual error patterns, not just the word "error"
    error_patterns = ["ERROR:", "Exception:", "Failed:", "Error occurred"]
    has_errors = any(pattern.lower() in response.lower() for pattern in error_patterns)
    assert not has_errors, "Response should not contain actual errors"


@pytest.mark.asyncio
@pytest.mark.skipif(skip_agency_tests, reason="OPENAI_API_KEY not set")
async def test_development_workflow(agency, test_queries):
    """Test development workflow functionality"""
    test_case = test_queries[4]
    run_result = await agency.get_response(test_case['query'])
    response = run_result.text if hasattr(run_result, 'text') else str(run_result)
    
    assert len(response) > 50, "Response should be substantial"
    # Check for actual error patterns, not just the word "error"
    error_patterns = ["ERROR:", "Exception:", "Failed:", "Error occurred"]
    has_errors = any(pattern.lower() in response.lower() for pattern in error_patterns)
    assert not has_errors, "Response should not contain actual errors"


@pytest.mark.asyncio
@pytest.mark.skipif(skip_agency_tests, reason="OPENAI_API_KEY not set")
async def test_all_queries_comprehensive(agency, test_queries):
    """Run all test queries and validate comprehensive functionality"""
    results = []
    
    for test in test_queries:
        try:
            # Execute the query
            run_result = await agency.get_response(test['query'])
            
            # Extract text from RunResult
            response = run_result.text if hasattr(run_result, 'text') else str(run_result)
            
            # Analyze response
            error_patterns = ["ERROR:", "Exception:", "Failed:", "Error occurred"]
            has_errors = any(pattern.lower() in response.lower() for pattern in error_patterns)
            success = len(response) > 50 and not has_errors
            quality_score = 8 if success else 4
            
            result = {
                "test_id": test['id'],
                "category": test['category'],
                "query": test['query'],
                "response": response[:500] + "..." if len(response) > 500 else response,
                "success": success,
                "quality_score": quality_score,
                "full_response": response
            }
            results.append(result)
            
        except Exception as e:
            result = {
                "test_id": test['id'],
                "category": test['category'],
                "query": test['query'],
                "response": f"ERROR: {str(e)}",
                "success": False,
                "quality_score": 0,
                "full_response": f"ERROR: {str(e)}"
            }
            results.append(result)
    
    # Assert that at least 3 out of 5 tests passed
    passed_tests = sum(1 for r in results if r['success'])
    assert passed_tests >= 3, f"At least 3 tests should pass, but only {passed_tests} passed"
    
    return results

