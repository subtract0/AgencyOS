import os
import sys
import time
from pathlib import Path
from unittest.mock import Mock

import pytest
from dotenv import load_dotenv

# Ensure project root is on sys.path so `agency_code_agent` can be imported
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load environment variables for tests (e.g., OPENAI_API_KEY)
load_dotenv()

# Skip spec traceability validation during tests for performance
# (validation takes ~30s on large codebases)
os.environ["SKIP_SPEC_TRACEABILITY"] = "true"

# Ensure logs directory exists for pytest log file
os.makedirs("logs", exist_ok=True)


@pytest.fixture(autouse=True, scope="function")
def cleanup_test_artifacts():
    """Global cleanup of test artifacts after each test."""
    yield
    # Clean up any test files that might be created
    test_files = ["fib.py", "test_fib.py", "test_file.py", "sample.py", "example.py"]
    for filename in test_files:
        if os.path.exists(filename):
            os.unlink(filename)

    # Clean up handoff logs created during tests
    handoff_logs_dir = "logs/handoffs"
    if os.path.exists(handoff_logs_dir):
        for filename in os.listdir(handoff_logs_dir):
            if filename.startswith("handoff_") and filename.endswith(".json"):
                file_path = os.path.join(handoff_logs_dir, filename)
                # Only clean up recent test files (avoid cleaning user's actual handoffs)
                try:
                    if os.path.exists(file_path) and os.path.getmtime(file_path) > (time.time() - 300):  # 5 minutes
                        os.unlink(file_path)
                except OSError:
                    pass  # File might be in use or doesn't exist, skip cleanup

    # Clean up snapshot logs created during tests
    snapshot_logs_dir = "logs/snapshots"
    if os.path.exists(snapshot_logs_dir):
        for filename in os.listdir(snapshot_logs_dir):
            if filename.startswith("snapshot_") and filename.endswith(".json"):
                file_path = os.path.join(snapshot_logs_dir, filename)
                # Only clean up recent test files
                try:
                    if os.path.exists(file_path) and os.path.getmtime(file_path) > (time.time() - 300):  # 5 minutes
                        os.unlink(file_path)
                except OSError:
                    pass  # File might be in use or doesn't exist, skip cleanup


@pytest.fixture
def temp_workspace(tmp_path):
    """Provide a temporary workspace directory for tests."""
    workspace = tmp_path / "test_workspace"
    workspace.mkdir(exist_ok=True)
    return workspace


@pytest.fixture
def temp_file_with_content(tmp_path):
    """Provide a temporary file with default content."""
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("Hello World\nThis is a test file\nWith multiple lines")
    return test_file


@pytest.fixture
def mock_agent_context():
    """Mock AgentContext for integration tests."""
    from datetime import datetime
    import uuid

    context = Mock()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_suffix = str(uuid.uuid4())[:8]
    context.session_id = f"test_session_{timestamp}_{unique_suffix}"
    context.store_memory = Mock()
    context.retrieve_memory = Mock(return_value=None)
    context.get_memories_by_tags = Mock(return_value=[])
    context.search_memories = Mock(return_value=[])
    context.get_session_memories = Mock(return_value=[])
    context.set_metadata = Mock()
    context.get_metadata = Mock(return_value=None)
    return context
