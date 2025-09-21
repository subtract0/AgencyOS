"""
Shared fixtures and mocks for unit tests.
All unit tests should use mocks to avoid actual LLM calls and file system operations.
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_agent_context():
    """Mock AgentContext for memory tests."""
    context = Mock()
    context.session_id = "test_session_123"
    context.store_memory = Mock()
    context.retrieve_memory = Mock(return_value=None)
    context.get_memories_by_tags = Mock(return_value=[])
    return context


@pytest.fixture
def mock_memory():
    """Mock Memory instance."""
    memory = Mock()
    memory.store = Mock()
    memory.retrieve = Mock(return_value=None)
    memory.get_by_tags = Mock(return_value=[])
    return memory


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for LLM interactions."""
    client = Mock()
    client.chat = Mock()
    client.chat.completions = Mock()
    client.chat.completions.create = Mock()

    # Mock response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "Mocked LLM response"
    mock_response.choices[0].message.function_call = None
    mock_response.choices[0].message.tool_calls = None

    client.chat.completions.create.return_value = mock_response
    return client


@pytest.fixture
def mock_agency_swarm_agent():
    """Mock Agency Swarm Agent to avoid actual LLM calls."""
    with patch('agency_swarm.Agent') as mock_agent_class:
        mock_agent = Mock()
        mock_agent.get_response = Mock()
        mock_agent.name = "TestAgent"
        mock_agent.description = "Test agent for unit tests"
        mock_agent.tools = []

        # Mock response with text attribute
        mock_response = Mock()
        mock_response.text = "Mocked agent response for testing"
        mock_agent.get_response.return_value = mock_response

        mock_agent_class.return_value = mock_agent
        yield mock_agent


@pytest.fixture
def mock_agency():
    """Mock Agency for testing without actual LLM calls."""
    with patch('agency_swarm.Agency') as mock_agency_class:
        mock_agency = Mock()
        mock_agency.get_response = Mock()

        # Mock response with text attribute
        mock_response = Mock()
        mock_response.text = "Mocked agency response for testing"
        mock_agency.get_response.return_value = mock_response

        mock_agency_class.return_value = mock_agency
        yield mock_agency


@pytest.fixture
def mock_tool_calls():
    """Mock tool calls and responses."""
    return {
        'bash': Mock(return_value={"stdout": "mocked bash output", "stderr": "", "return_code": 0}),
        'read': Mock(return_value="mocked file content"),
        'write': Mock(return_value="File written successfully"),
        'grep': Mock(return_value=["file1.py:10:    # TODO: implement this", "file2.py:25:    # TODO: fix bug"]),
        'ls': Mock(return_value=["file1.py", "file2.py", "test.py"]),
        'glob': Mock(return_value=["src/main.py", "tests/test_main.py"]),
        'git': Mock(return_value="On branch main\nnothing to commit, working tree clean"),
        'web_search': Mock(return_value="Mock search results about Agency Swarm framework"),
    }


@pytest.fixture
def mock_system_hooks():
    """Mock system hooks."""
    reminder_hook = Mock()
    reminder_hook.pre_call = Mock()
    reminder_hook.post_call = Mock()

    memory_hook = Mock()
    memory_hook.pre_call = Mock()
    memory_hook.post_call = Mock()

    return {
        'reminder_hook': reminder_hook,
        'memory_hook': memory_hook
    }


@pytest.fixture
def mock_environment_vars():
    """Mock environment variables for tests."""
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_key_123',
        'ANTHROPIC_API_KEY': 'test_anthropic_key_123',
        'TEST_MODE': 'true'
    }):
        yield


@pytest.fixture(autouse=True)
def fast_test_setup(mock_environment_vars):
    """Auto-applied fixture to ensure all unit tests run fast."""
    # Mock time-consuming operations
    with patch('time.sleep'), \
         patch('asyncio.sleep'), \
         patch('requests.get') as mock_get, \
         patch('httpx.AsyncClient') as mock_httpx:

        # Mock HTTP responses
        mock_response = Mock()
        mock_response.text = "Mock HTTP response"
        mock_response.json.return_value = {"status": "mocked"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Mock async HTTP client
        mock_client = Mock()
        mock_client.get = Mock()
        mock_client.get.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client

        yield


@pytest.fixture
def sample_test_queries():
    """Sample test queries for agency functionality testing."""
    return [
        {
            "id": 1,
            "category": "File Operations",
            "query": "List files in the current directory",
            "expected_tools": ["ls"],
            "mock_response": "Found 5 Python files in current directory"
        },
        {
            "id": 2,
            "category": "Code Search",
            "query": "Search for TODO comments",
            "expected_tools": ["grep"],
            "mock_response": "Found 3 TODO comments in 2 files"
        },
        {
            "id": 3,
            "category": "File Creation",
            "query": "Create a simple script",
            "expected_tools": ["write", "todo_write"],
            "mock_response": "Successfully created script.py with basic functionality"
        }
    ]


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create temporary directory for file system tests."""
    # Change to temp directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    # Create some test files
    (tmp_path / "test_file.py").write_text("# Test Python file\nprint('hello')")
    (tmp_path / "README.md").write_text("# Test Project\nThis is a test.")

    yield tmp_path

    # Restore original directory
    os.chdir(original_cwd)