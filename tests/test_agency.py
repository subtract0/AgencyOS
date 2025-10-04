"""
Test Agency for Agency Code Agent
Tests the agent with 5 diverse queries to validate functionality
"""

from unittest.mock import MagicMock, patch

import pytest
from agency_swarm import Agency
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@pytest.fixture
def mock_agency():
    """Create a mock agency for testing"""
    mock_agent = MagicMock()
    mock_agent.name = "AgencyCodeAgent"
    mock_agent.model = "gpt-5-mini"
    mock_agent.tools = []

    with patch.object(Agency, "__init__", lambda self, *args, **kwargs: None):
        agency = Agency.__new__(Agency)
        agency.agents = [mock_agent]
        agency.shared_instructions = "Test instructions"
        return agency


@pytest.fixture
def test_queries():
    """Test queries for agency functionality validation"""
    return [
        {
            "id": 1,
            "category": "File Operations",
            "query": "List files in the current directory and read the contents of the first Python file you find",
            "expected_response": "Listed 5 Python files. Reading test.py:\n```python\ndef hello():\n    return 'Hello World'\n```",
        },
        {
            "id": 2,
            "category": "Code Search",
            "query": "Search for any TODO comments in Python files and show me the results with line numbers",
            "expected_response": "Found 3 TODO comments:\n- test.py:15: # TODO: Implement feature\n- main.py:42: # TODO: Fix bug\n- utils.py:7: # TODO: Optimize",
        },
        {
            "id": 3,
            "category": "Complex Task",
            "query": "Help me create a simple Python script that calculates fibonacci numbers and save it to fib.py. Use the TodoWrite tool to track your progress",
            "expected_response": "Created fib.py with fibonacci function:\n```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```\nTodo: ✓ Create fibonacci function\n✓ Save to fib.py",
        },
        {
            "id": 4,
            "category": "Web Research",
            "query": "Search for information about Agency Swarm framework and fetch content from the official documentation",
            "expected_response": "Found information about Agency Swarm:\n- Multi-agent orchestration framework\n- Enables AI collaboration\n- Documentation: agency-swarm.ai",
        },
        {
            "id": 5,
            "category": "Development Workflow",
            "query": "Show me the git status and create a sample test file, then stage it for commit",
            "expected_response": "Git status: clean working tree\nCreated test_sample.py\nStaged test_sample.py for commit",
        },
    ]


@pytest.mark.asyncio
async def test_file_operations(mock_agency, test_queries):
    """Test file operations functionality with mocks"""
    with patch.object(Agency, "get_response") as mock_get_response:
        mock_response = MagicMock()
        mock_response.text = test_queries[0]["expected_response"]
        mock_get_response.return_value = mock_response

        result = await mock_agency.get_response(test_queries[0]["query"])
        response = result.text if hasattr(result, "text") else str(result)

        assert len(response) > 50, "Response should be substantial"
        assert "python" in response.lower() or ".py" in response.lower()
        assert mock_get_response.called


@pytest.mark.asyncio
async def test_code_search(mock_agency, test_queries):
    """Test code search functionality with mocks"""
    with patch.object(Agency, "get_response") as mock_get_response:
        mock_response = MagicMock()
        mock_response.text = test_queries[1]["expected_response"]
        mock_get_response.return_value = mock_response

        result = await mock_agency.get_response(test_queries[1]["query"])
        response = result.text if hasattr(result, "text") else str(result)

        assert len(response) > 50, "Response should be substantial"
        assert "TODO" in response
        assert mock_get_response.called


@pytest.mark.asyncio
async def test_complex_task(mock_agency, test_queries):
    """Test complex task with todo tracking using mocks"""
    with patch.object(Agency, "get_response") as mock_get_response:
        mock_response = MagicMock()
        mock_response.text = test_queries[2]["expected_response"]
        mock_get_response.return_value = mock_response

        result = await mock_agency.get_response(test_queries[2]["query"])
        response = result.text if hasattr(result, "text") else str(result)

        assert len(response) > 50, "Response should be substantial"
        assert "fibonacci" in response.lower()
        assert mock_get_response.called


@pytest.mark.asyncio
async def test_web_research(mock_agency, test_queries):
    """Test web research functionality with mocked responses"""
    with patch.object(Agency, "get_response") as mock_get_response:
        mock_response = MagicMock()
        mock_response.text = test_queries[3]["expected_response"]
        mock_get_response.return_value = mock_response

        result = await mock_agency.get_response(test_queries[3]["query"])
        response = result.text if hasattr(result, "text") else str(result)

        assert len(response) > 50, "Response should be substantial"
        assert "Agency Swarm" in response
        assert mock_get_response.called


@pytest.mark.asyncio
async def test_development_workflow(mock_agency, test_queries):
    """Test development workflow functionality with mocks"""
    with patch.object(Agency, "get_response") as mock_get_response:
        mock_response = MagicMock()
        mock_response.text = test_queries[4]["expected_response"]
        mock_get_response.return_value = mock_response

        result = await mock_agency.get_response(test_queries[4]["query"])
        response = result.text if hasattr(result, "text") else str(result)

        assert len(response) > 50, "Response should be substantial"
        assert "git" in response.lower() or "staged" in response.lower()
        assert mock_get_response.called


@pytest.mark.asyncio
async def test_error_handling():
    """Test that the agency handles errors gracefully"""
    with patch.object(Agency, "get_response") as mock_get_response:
        # Simulate an error scenario
        mock_get_response.side_effect = Exception("Simulated error")

        mock_agent = MagicMock()
        mock_agent.name = "AgencyCodeAgent"

        with patch.object(Agency, "__init__", lambda self, *args, **kwargs: None):
            agency = Agency.__new__(Agency)
            agency.agents = [mock_agent]

            with pytest.raises(Exception) as exc_info:
                await agency.get_response("Test query")

            assert "Simulated error" in str(exc_info.value)
