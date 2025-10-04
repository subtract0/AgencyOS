"""
Shared test fixtures for Agency test suite.

Provides common fixtures used across unit, integration, and e2e tests.
"""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Provide a temporary directory for tests.

    Automatically cleaned up after test completion.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file(temp_dir: Path) -> Path:
    """
    Provide a temporary file for tests.

    File is created in a temporary directory.
    """
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("test content")
    return file_path


@pytest.fixture
def mock_agent_context():
    """
    Provide a mock AgentContext for unit tests.

    DEPRECATED: Use create_test_agent_context() for constitutional compliance.
    This fixture violates Article II (Mocks ≠ Green amendment).

    Avoids loading real memory stores and configuration.
    """
    from unittest.mock import Mock

    context = Mock()
    context.store_memory = Mock()
    context.search_memories = Mock(return_value=[])
    context.get_session_id = Mock(return_value="test-session-123")

    return context


@pytest.fixture
def constitutional_test_agent():
    """
    Provide a REAL Agent instance for testing (constitutional compliance).

    Replaces mock_agent fixtures which violate Article II.
    See tests/fixtures/constitutional_test_agents.py for details.
    """
    from tests.fixtures.constitutional_test_agents import create_constitutional_test_agent

    def _create_agent(name: str = "TestAgent", **kwargs):
        return create_constitutional_test_agent(name, **kwargs)

    return _create_agent


@pytest.fixture
def constitutional_agent_context():
    """
    Provide a REAL AgentContext for testing (constitutional compliance).

    Uses InMemoryStore for fast, isolated testing.
    Replaces mock_agent_context which violates Article II.
    """
    from tests.fixtures.constitutional_test_agents import create_test_agent_context

    def _create_context(session_id: str | None = None):
        return create_test_agent_context(session_id)

    return _create_context


@pytest.fixture
def sample_code():
    """Provide sample Python code for testing."""
    return '''
def calculate_total(items: list[dict]) -> float:
    """Calculate total price from items."""
    return sum(item.get('price', 0) for item in items)

def validate_email(email: str) -> bool:
    """Validate email format."""
    return '@' in email and '.' in email.split('@')[1]
'''


@pytest.fixture
def sample_test_code():
    """Provide sample test code for testing."""
    return """
import pytest

@pytest.mark.unit
def test_calculate_total():
    items = [{'price': 10}, {'price': 20}]
    assert calculate_total(items) == 30

@pytest.mark.unit
def test_validate_email():
    assert validate_email('test@example.com')
    assert not validate_email('invalid-email')
"""


# Performance measurement helpers
@pytest.fixture
def benchmark_timer():
    """
    Provide a simple timer for performance benchmarks.

    Usage:
        with benchmark_timer() as timer:
            expensive_operation()
        assert timer.elapsed < 1.0  # Must complete in <1s
    """
    import time
    from contextlib import contextmanager

    @contextmanager
    def timer():
        class Timer:
            elapsed = 0.0

        t = Timer()
        start = time.perf_counter()
        yield t
        t.elapsed = time.perf_counter() - start

    return timer
