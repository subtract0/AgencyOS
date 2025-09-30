"""
Test configuration for DSPy agents.

Provides proper DSPy initialization for tests and mock setups.
"""

import os
import pytest
from unittest.mock import Mock, MagicMock, patch

# Set test environment
os.environ["OPENAI_API_KEY"] = "test-key-for-dspy"
os.environ["DSPY_MODEL"] = "openai/gpt-4o-mini"
os.environ["AUTO_INIT_DSPY"] = "false"  # Disable auto-init for tests

try:
    import dspy
    from dspy_agents.config import DSPyConfig
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False

# Global flag to prevent real API calls in tests
MOCK_LM_ENABLED = True


@pytest.fixture(autouse=True)
def mock_dspy_for_tests():
    """Automatically mock DSPy for all tests to prevent real API calls."""
    if not DSPY_AVAILABLE or not MOCK_LM_ENABLED:
        yield
        return

    # Create a mock LM that returns predictable responses
    mock_lm = Mock()
    mock_lm.model = "test-model"
    mock_lm.temperature = 1.0
    mock_lm.max_tokens = 4096

    # Mock the LM __call__ to return test data
    def mock_lm_call(*args, **kwargs):
        # Return mock response based on the prompt
        return Mock(
            completions=[Mock(text="TestTool")],
            tool_name="TestTool",
            tool_description="Test tool description",
            parameters=[],
            test_cases=["test1"],
            implementation_plan=["step1"],
            design_rationale="Mock rationale"
        )

    mock_lm.__call__ = mock_lm_call

    # Mock DSPy's LM class
    with patch('dspy.LM') as MockLM:
        MockLM.return_value = mock_lm

        # Configure DSPy with the mock
        dspy.configure(lm=mock_lm)

        # Also patch DSPyConfig to use the mock
        with patch.object(DSPyConfig, 'initialize', return_value=True):
            with patch.object(DSPyConfig, 'get_lm', return_value=mock_lm):
                DSPyConfig._initialized = True
                DSPyConfig._lm_cache['test-model'] = mock_lm
                yield
                DSPyConfig.reset()


@pytest.fixture(autouse=True)
def reset_dspy_config():
    """Reset DSPy configuration before each test."""
    if DSPY_AVAILABLE:
        DSPyConfig.reset()
    yield
    if DSPY_AVAILABLE:
        DSPyConfig.reset()


@pytest.fixture
def mock_dspy_lm():
    """Provide a mock DSPy Language Model for testing."""
    if not DSPY_AVAILABLE:
        return None

    mock_lm = Mock()
    mock_lm.generate = Mock(return_value={"choices": [{"text": "Mock response"}]})
    mock_lm.model = "test-model"

    # Configure DSPy with mock
    dspy.configure(lm=mock_lm)
    return mock_lm


@pytest.fixture
def initialized_dspy():
    """Initialize DSPy with test configuration."""
    if not DSPY_AVAILABLE:
        pytest.skip("DSPy not available")

    # Use a mock LM for testing
    mock_lm = Mock()
    mock_lm.model = "test-model"
    mock_lm.__call__ = Mock(return_value="Test response")

    try:
        import dspy
        dspy.configure(lm=mock_lm)
        return True
    except Exception as e:
        pytest.skip(f"Could not initialize DSPy: {e}")


@pytest.fixture
def dspy_test_context():
    """Provide a complete test context for DSPy agents."""
    return {
        "repository_root": "/test/repo",
        "session_id": "test-session-123",
        "existing_tools": ["tool1", "tool2"],
        "constitutional_requirements": [
            "Article I - Complete Context",
            "Article II - 100% Verification",
            "Article III - Automated Enforcement",
            "Article IV - Continuous Learning",
            "Article V - Spec-Driven Development"
        ]
    }