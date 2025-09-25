import os
import sys
import time
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Ensure project root is on sys.path so `agency_code_agent` can be imported
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load environment variables for tests (e.g., OPENAI_API_KEY)
load_dotenv()

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
                if os.path.getmtime(file_path) > (time.time() - 300):  # 5 minutes
                    try:
                        os.unlink(file_path)
                    except OSError:
                        pass  # File might be in use, skip cleanup

    # Clean up snapshot logs created during tests
    snapshot_logs_dir = "logs/snapshots"
    if os.path.exists(snapshot_logs_dir):
        for filename in os.listdir(snapshot_logs_dir):
            if filename.startswith("snapshot_") and filename.endswith(".json"):
                file_path = os.path.join(snapshot_logs_dir, filename)
                # Only clean up recent test files
                if os.path.getmtime(file_path) > (time.time() - 300):  # 5 minutes
                    try:
                        os.unlink(file_path)
                    except OSError:
                        pass  # File might be in use, skip cleanup


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
