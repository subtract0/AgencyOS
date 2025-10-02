import os
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

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

# ============================================================================
# STATE-OF-THE-ART TEST ARCHITECTURE CONFIGURATION
# ============================================================================


def pytest_collection_modifyitems(items):
    """
    Auto-categorize tests by directory structure and enforce timeouts.

    Three-tier architecture:
    - unit/: Fast isolated tests (2s timeout, mocked externals)
    - integration/: Component interaction tests (10s timeout)
    - e2e/: End-to-end scenarios (30s timeout)

    Tests are automatically marked based on their location, with sensible
    timeout defaults to prevent test suite hangs.
    """
    for item in items:
        test_path = str(item.fspath)

        # Auto-categorize by path
        if "/unit/" in test_path or "/tests/unit/" in test_path:
            item.add_marker(pytest.mark.unit)
            # Unit tests should be fast (2 seconds max)
            if not any(m.name == "timeout" for m in item.iter_markers()):
                item.add_marker(pytest.mark.timeout(2))

        elif "/integration/" in test_path or "/tests/integration/" in test_path:
            item.add_marker(pytest.mark.integration)
            # Integration tests can be slower (10 seconds max)
            if not any(m.name == "timeout" for m in item.iter_markers()):
                item.add_marker(pytest.mark.timeout(10))

        elif "/e2e/" in test_path or "/tests/e2e/" in test_path:
            item.add_marker(pytest.mark.e2e)
            # E2E tests can be much slower (30 seconds max)
            if not any(m.name == "timeout" for m in item.iter_markers()):
                item.add_marker(pytest.mark.timeout(30))

        elif "/benchmark/" in test_path or "/tests/benchmark/" in test_path:
            item.add_marker(pytest.mark.benchmark)
            # Benchmarks can take longer
            if not any(m.name == "timeout" for m in item.iter_markers()):
                item.add_marker(pytest.mark.timeout(60))

        else:
            # Tests not in categorized directories default to unit with timeout
            # This ensures uncategorized tests don't hang the suite
            if not any(m.name in ("unit", "integration", "e2e", "benchmark") for m in item.iter_markers()):
                item.add_marker(pytest.mark.unit)
            if not any(m.name == "timeout" for m in item.iter_markers()):
                item.add_marker(pytest.mark.timeout(5))

        # Track slow tests for optimization opportunities
        item.stash_start_time = None


def pytest_runtest_setup(item):
    """Record test start time for performance tracking."""
    item.stash_start_time = time.time()


def pytest_runtest_teardown(item, nextitem):
    """Track slow tests for future optimization."""
    if item.stash_start_time:
        duration = time.time() - item.stash_start_time
        # Flag tests taking >1s for review (potential optimization targets)
        if duration > 1.0 and "benchmark" not in [m.name for m in item.iter_markers()]:
            # Store in logs for analysis
            slow_tests_log = Path("logs/slow_tests.log")
            slow_tests_log.parent.mkdir(exist_ok=True)
            with open(slow_tests_log, "a") as f:
                f.write(f"{duration:.2f}s - {item.nodeid}\n")


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


# ============================================================================
# GLOBAL MOCKING FOR UNIT TESTS (Prevent Expensive External API Calls)
# ============================================================================


@pytest.fixture(autouse=True)
def mock_expensive_external_apis(request):
    """
    Automatically mock expensive external API calls in unit tests.

    This fixture activates only for tests marked as 'unit' to prevent
    accidental external API calls during unit testing.

    Mocked services:
    - OpenAI API (GPT-5, GPT-4, completions, embeddings)
    - Firestore (Google Cloud Firestore)
    - HTTP requests (requests library, urllib)
    - File system operations marked as expensive

    Integration and E2E tests are NOT mocked to allow real API testing.
    """
    # Only mock for unit tests
    if "unit" not in [m.name for m in request.node.iter_markers()]:
        yield
        return

    # Mock OpenAI API
    mock_openai_response = MagicMock()
    mock_openai_response.choices = [
        MagicMock(
            message=MagicMock(content="Mocked response"),
            finish_reason="stop"
        )
    ]
    mock_openai_response.usage = MagicMock(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30
    )
    mock_openai_response.model = "gpt-5-mini"

    # Mock Firestore
    mock_firestore_client = MagicMock()
    mock_firestore_collection = MagicMock()
    mock_firestore_document = MagicMock()
    mock_firestore_client.collection.return_value = mock_firestore_collection
    mock_firestore_collection.document.return_value = mock_firestore_document
    mock_firestore_document.get.return_value = MagicMock(exists=False)

    # Mock requests library
    mock_requests_response = MagicMock()
    mock_requests_response.status_code = 200
    mock_requests_response.json.return_value = {"mocked": True}
    mock_requests_response.text = "Mocked response"

    patches = [
        # OpenAI API
        patch("openai.OpenAI", return_value=MagicMock(
            chat=MagicMock(
                completions=MagicMock(
                    create=MagicMock(return_value=mock_openai_response)
                )
            ),
            embeddings=MagicMock(
                create=MagicMock(return_value=MagicMock(
                    data=[MagicMock(embedding=[0.1] * 1536)]
                ))
            )
        )),
        # Firestore
        patch("google.cloud.firestore.Client", return_value=mock_firestore_client),
        # Requests library
        patch("requests.get", return_value=mock_requests_response),
        patch("requests.post", return_value=mock_requests_response),
        patch("requests.put", return_value=mock_requests_response),
        patch("requests.delete", return_value=mock_requests_response),
    ]

    # Start all patches
    mocks = [p.start() for p in patches]

    yield

    # Stop all patches
    for p in patches:
        p.stop()


@pytest.fixture
def isolated_test_env(monkeypatch):
    """
    Isolate test environment variables to prevent cross-test pollution.

    Ensures tests don't affect each other through environment state.
    """
    # Save original environment
    original_env = os.environ.copy()

    # Provide clean test-specific environment
    test_env = {
        "OPENAI_API_KEY": "test-key-12345",
        "SKIP_SPEC_TRACEABILITY": "true",
        "USE_ENHANCED_MEMORY": "false",  # Disable vector store in unit tests
        "FRESH_USE_FIRESTORE": "false",
    }

    for key, value in test_env.items():
        monkeypatch.setenv(key, value)

    yield test_env

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def performance_tracker():
    """
    Track test performance metrics for optimization insights.

    Usage:
        def test_something(performance_tracker):
            with performance_tracker.track("operation_name"):
                # ... expensive operation
            # Metrics auto-logged to logs/performance.log
    """
    class PerformanceTracker:
        def __init__(self):
            self.metrics = {}
            self.log_file = Path("logs/performance.log")
            self.log_file.parent.mkdir(exist_ok=True)

        def track(self, operation_name):
            import contextlib

            @contextlib.contextmanager
            def _tracker():
                start = time.time()
                yield
                duration = time.time() - start
                self.metrics[operation_name] = duration
                with open(self.log_file, "a") as f:
                    f.write(f"{operation_name}: {duration:.4f}s\n")

            return _tracker()

    return PerformanceTracker()
