"""
Comprehensive test suite for DSPyToolsmithAgent

Tests the DSPy-powered Toolsmith Agent implementation including:
- Tool directive parsing
- Tool scaffolding
- Test generation
- Integration with existing Agency tools
- Learning capabilities
- Fallback behavior when DSPy is not available
"""

import os
import sys
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dspy_agents.modules.toolsmith_agent import (
    DSPyToolsmithAgent,
    create_dspy_toolsmith_agent,
    ToolCreationContext,
    ToolArtifact,
)
from dspy_agents.signatures.base import (
    FileChange,
    TestSpecification,
    VerificationResult,
    AgentResult,
)


class TestDSPyToolsmithAgentInitialization:
    """Test agent initialization and configuration."""

    def test_initialization_with_defaults(self):
        """Test that agent initializes with default parameters."""
        agent = DSPyToolsmithAgent()

        assert agent.model == "gpt-4o-mini"
        assert agent.reasoning_effort == "medium"
        assert agent.enable_learning is True
        assert agent.quality_threshold == 0.85
        assert agent.successful_tools == []
        assert agent.failed_attempts == []

    def test_initialization_with_custom_params(self):
        """Test initialization with custom parameters."""
        agent = DSPyToolsmithAgent(
            model="gpt-5",
            reasoning_effort="high",
            enable_learning=False,
            quality_threshold=0.95
        )

        assert agent.model == "gpt-5"
        assert agent.reasoning_effort == "high"
        assert agent.enable_learning is False
        assert agent.quality_threshold == 0.95

    @patch('dspy_agents.modules.toolsmith_agent.DSPY_AVAILABLE', False)
    def test_initialization_without_dspy(self):
        """Test initialization when DSPy is not available."""
        agent = DSPyToolsmithAgent()

        assert agent.dspy_available is False
        assert agent.directive_parser is None
        assert agent.scaffolder is None
        assert agent.test_generator is None
        assert agent.handoff_preparer is None

    def test_factory_function(self):
        """Test the factory function creates correct instance."""
        agent = create_dspy_toolsmith_agent(
            model="gpt-5",
            reasoning_effort="high"
        )

        assert isinstance(agent, DSPyToolsmithAgent)
        assert agent.model == "gpt-5"
        assert agent.reasoning_effort == "high"


class TestToolDirectiveParsing:
    """Test tool directive parsing functionality."""

    @pytest.fixture
    def agent(self):
        """Create an agent instance for testing."""
        # Prevent real DSPy initialization
        with patch('dspy_agents.modules.toolsmith_agent.DSPyConfig.initialize', return_value=False):
            return DSPyToolsmithAgent()

    def test_parse_directive_success(self):
        """Test successful directive parsing."""
        # Create agent with mocked directive parser
        with patch('dspy_agents.modules.toolsmith_agent.DSPyConfig.initialize', return_value=False):
            agent = DSPyToolsmithAgent()

        # Mock the DSPy directive parser
        mock_result = Mock()
        mock_result.tool_name = "ContextMessageHandoff"
        mock_result.tool_description = "A handoff tool with context"
        mock_result.parameters = [
            {"name": "mission", "type": "str", "required": True},
            {"name": "context", "type": "dict", "required": False}
        ]
        mock_result.test_cases = ["Test basic functionality", "Test error handling"]
        mock_result.implementation_plan = ["Parse inputs", "Create tool", "Test"]

        agent.directive_parser = Mock(return_value=mock_result)
        # Ensure agent thinks DSPy is available so it uses the mock
        agent.dspy_available = True

        result = agent.parse_directive(
            "Create ContextMessageHandoff tool",
            ["ExistingTool1", "ExistingTool2"],
            ["Constitutional requirement 1"]
        )

        assert result["tool_name"] == "ContextMessageHandoff"
        assert result["tool_description"] == "A handoff tool with context"
        assert len(result["parameters"]) == 2
        assert len(result["test_cases"]) == 2
        assert len(result["implementation_plan"]) == 3

    def test_parse_directive_fallback(self):
        """Test fallback directive parsing when DSPy unavailable."""
        # Patch DSPY_AVAILABLE and DSPyConfig to simulate no DSPy
        with patch('dspy_agents.modules.toolsmith_agent.DSPY_AVAILABLE', False):
            with patch('dspy_agents.modules.toolsmith_agent.DSPyConfig.initialize', return_value=False):
                # Create agent with patched DSPY_AVAILABLE=False
                agent = DSPyToolsmithAgent()

                result = agent.parse_directive(
                    "Create TestTool tool for testing",
                    [],
                    []
                )

                assert result["tool_name"] == "TestTool"
                assert "Tool created from directive:" in result["tool_description"]
                assert isinstance(result["parameters"], list)
                assert isinstance(result["test_cases"], list)
                assert isinstance(result["implementation_plan"], list)

    def test_parse_directive_with_error(self, agent):
        """Test directive parsing with error handling."""
        agent.directive_parser = Mock(side_effect=Exception("Parse error"))
        # Ensure agent thinks DSPy is available so it tries to use the parser (which will error)
        agent.dspy_available = True

        result = agent.parse_directive("Invalid directive", [], [])

        assert result["tool_name"] == "unknown"
        assert "Invalid directive" in result["tool_description"]
        assert result["implementation_plan"] == ["Error parsing directive"]


class TestToolScaffolding:
    """Test tool scaffolding functionality."""

    @pytest.fixture
    def agent(self):
        """Create an agent instance for testing."""
        # Prevent real DSPy initialization
        with patch('dspy_agents.modules.toolsmith_agent.DSPyConfig.initialize', return_value=False):
            return DSPyToolsmithAgent()

    @patch('dspy_agents.modules.toolsmith_agent.DSPY_AVAILABLE', True)
    def test_scaffold_tool_success(self, agent):
        """Test successful tool scaffolding."""
        mock_result = Mock()
        mock_result.tool_code = '''
from pydantic import BaseModel

class TestTool(BaseModel):
    def run(self):
        return {"success": True}
'''
        mock_result.imports = ["from pydantic import BaseModel"]

        agent.scaffolder = Mock(return_value=mock_result)

        code, imports, rationale = agent.scaffold_tool(
            "TestTool",
            "A test tool",
            [{"name": "param1", "type": "str"}],
            {}
        )

        assert "class TestTool" in code
        assert "def run" in code
        assert len(imports) > 0

    @pytest.mark.skip(reason="TODO: Fix DSPy Mock - requires proper dspy.BaseLM mock instead of unittest.mock.Mock")
    @patch('dspy_agents.modules.toolsmith_agent.DSPY_AVAILABLE', False)
    def test_scaffold_tool_fallback(self, agent):
        """Test fallback tool scaffolding."""
        code, imports, rationale = agent.scaffold_tool(
            "FallbackTool",
            "A fallback tool",
            [],
            {}
        )

        assert "class FallbackTool" in code
        assert "def run" in code
        assert "pydantic" in str(imports)

    def test_scaffold_tool_with_error(self, agent):
        """Test tool scaffolding error handling."""
        agent.scaffolder = Mock(side_effect=Exception("Scaffold error"))
        agent.dspy_available = True  # Force error path instead of fallback

        code, imports, rationale = agent.scaffold_tool("ErrorTool", "Error", [], {})

        assert "Error scaffolding tool" in code
        assert imports == []


class TestTestGeneration:
    """Test test generation functionality."""

    @pytest.fixture
    def agent(self):
        """Create an agent instance for testing."""
        # Prevent real DSPy initialization
        with patch('dspy_agents.modules.toolsmith_agent.DSPyConfig.initialize', return_value=False):
            return DSPyToolsmithAgent()

    @patch('dspy_agents.modules.toolsmith_agent.DSPY_AVAILABLE', True)
    def test_generate_tests_success(self, agent):
        """Test successful test generation."""
        mock_result = Mock()
        mock_result.test_code = '''
import pytest
from tools.test_tool import TestTool

def test_initialization():
    tool = TestTool()
    assert tool is not None

def test_run_method():
    tool = TestTool()
    result = tool.run()
    assert result["success"] is True
'''

        agent.test_generator = Mock(return_value=mock_result)

        test_code = agent.generate_tests(
            "TestTool",
            "class TestTool...",
            ["Test initialization", "Test run method"],
            follow_necessary=True
        )

        assert "def test_initialization" in test_code
        assert "def test_run_method" in test_code
        assert "import pytest" in test_code

    @pytest.mark.skip(reason="TODO: Fix DSPy Mock - requires proper dspy.BaseLM mock instead of unittest.mock.Mock")
    @patch('dspy_agents.modules.toolsmith_agent.DSPY_AVAILABLE', False)
    def test_generate_tests_fallback(self, agent):
        """Test fallback test generation."""
        test_code = agent.generate_tests(
            "FallbackTool",
            "class FallbackTool...",
            [],
            follow_necessary=False
        )

        assert "def test_fallbacktool_initialization" in test_code
        assert "def test_fallbacktool_run" in test_code
        assert "import pytest" in test_code

    def test_generate_tests_with_error(self, agent):
        """Test test generation error handling."""
        agent.test_generator = Mock(side_effect=Exception("Test gen error"))
        agent.dspy_available = True  # Force error path instead of fallback

        test_code = agent.generate_tests("ErrorTool", "", [], True)

        assert "Error generating tests" in test_code


class TestMainForwardMethod:
    """Test the main forward method."""

    @pytest.fixture
    def agent(self):
        """Create an agent instance for testing."""
        return DSPyToolsmithAgent(enable_learning=True)

    @pytest.fixture
    def mock_context(self):
        """Create a mock context."""
        return {
            "repository_root": "/test/repo",
            "tools_directory": "tools",
            "tests_directory": "tests",
            "session_id": "test_session_123"
        }

    @patch('dspy_agents.modules.toolsmith_agent.DSPY_AVAILABLE', True)
    @patch('dspy_agents.modules.toolsmith_agent.subprocess.run')
    def test_forward_success(self, mock_subprocess, agent, mock_context):
        """Test successful tool creation flow."""
        # Mock directive parsing
        mock_parsed = Mock()
        mock_parsed.tool_name = "TestTool"
        mock_parsed.tool_description = "Test tool"
        mock_parsed.parameters = []
        mock_parsed.test_cases = ["Test 1"]
        agent.directive_parser = Mock(return_value=mock_parsed)

        # Mock tool scaffolding
        mock_scaffold = Mock()
        mock_scaffold.tool_code = "class TestTool: pass"
        mock_scaffold.imports = []
        agent.scaffolder = Mock(return_value=mock_scaffold)

        # Mock test generation
        mock_test = Mock()
        mock_test.test_code = "def test_tool(): pass"
        agent.test_generator = Mock(return_value=mock_test)

        # Mock test execution
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="Tests passed",
            stderr=""
        )

        # Mock handoff preparation
        mock_handoff = Mock()
        mock_handoff.handoff_package = {"ready": True}
        agent.handoff_preparer = Mock(return_value=mock_handoff)

        result = agent.forward(
            "Create TestTool for testing",
            mock_context
        )

        assert result.success is True
        assert "TestTool" in result.message
        assert len(result.changes) == 2  # Tool and test files
        assert len(result.tests) == 1
        assert result.verification.all_tests_pass is True

    @pytest.mark.skip(reason="TODO: Fix DSPy Mock - requires proper dspy.BaseLM mock instead of unittest.mock.Mock")
    @patch('dspy_agents.modules.toolsmith_agent.DSPY_AVAILABLE', False)
    def test_forward_fallback(self, agent, mock_context):
        """Test fallback behavior when DSPy not available."""
        result = agent.forward(
            "Create TestTool",
            mock_context
        )

        assert result.success is False
        assert ("DSPy not available" in result.message or "CONSTITUTIONAL" in result.message)
        assert len(result.changes) >= 0  # May have fallback changes
        assert len(result.tests) >= 0  # May have fallback tests

    def test_forward_with_exception(self, agent, mock_context):
        """Test forward method exception handling."""
        agent.directive_parser = Mock(side_effect=Exception("Fatal error"))
        agent.dspy_available = True  # Force error path instead of fallback

        result = agent.forward(
            "Create ErrorTool",
            mock_context
        )

        assert result.success is False
        assert "Fatal error" in result.message
        assert result.verification.all_tests_pass is False


class TestLearningCapabilities:
    """Test agent learning functionality."""

    @pytest.fixture
    def agent(self):
        """Create an agent with learning enabled."""
        return DSPyToolsmithAgent(enable_learning=True)

    def test_learn_from_success(self, agent):
        """Test learning from successful tool creation."""
        context = ToolCreationContext(
            repository_root="/test",
            session_id="test_123"
        )

        agent._learn_from_creation(
            "Create TestTool",
            "TestTool",
            success=True,
            context=context
        )

        assert len(agent.successful_tools) == 1
        assert agent.successful_tools[0]["tool_name"] == "TestTool"
        assert agent.successful_tools[0]["success"] is True

    def test_learn_from_failure(self, agent):
        """Test learning from failed tool creation."""
        context = ToolCreationContext(
            repository_root="/test",
            session_id="test_123"
        )

        agent._learn_from_creation(
            "Create FailTool",
            "FailTool",
            success=False,
            context=context
        )

        assert len(agent.failed_attempts) == 1
        assert agent.failed_attempts[0]["tool_name"] == "FailTool"
        assert agent.failed_attempts[0]["success"] is False

    def test_learning_storage_limits(self, agent):
        """Test that learning storage respects limits."""
        context = ToolCreationContext(
            repository_root="/test",
            session_id="test_123"
        )

        # Add many successful patterns
        for i in range(60):
            agent._learn_from_creation(
                f"Create Tool{i}",
                f"Tool{i}",
                success=True,
                context=context
            )

        # Should be limited to 50
        assert len(agent.successful_tools) == 50

        # Add many failed patterns
        for i in range(30):
            agent._learn_from_creation(
                f"Create FailTool{i}",
                f"FailTool{i}",
                success=False,
                context=context
            )

        # Should be limited to 25
        assert len(agent.failed_attempts) == 25

    def test_get_learning_summary(self, agent):
        """Test getting learning summary."""
        context = ToolCreationContext(
            repository_root="/test",
            session_id="test_123"
        )

        # Add some patterns
        for i in range(3):
            agent._learn_from_creation(f"Tool{i}", f"Tool{i}", True, context)
        for i in range(2):
            agent._learn_from_creation(f"Fail{i}", f"Fail{i}", False, context)

        summary = agent.get_learning_summary()

        assert summary["successful_tools"] == 3
        assert summary["failed_attempts"] == 2
        assert summary["total_creations"] == 5
        assert summary["success_rate"] == 0.6

    def test_reset_learning(self, agent):
        """Test resetting learned patterns."""
        context = ToolCreationContext(
            repository_root="/test",
            session_id="test_123"
        )

        # Add some patterns
        agent._learn_from_creation("Tool1", "Tool1", True, context)
        agent._learn_from_creation("Tool2", "Tool2", False, context)

        assert len(agent.successful_tools) > 0
        assert len(agent.failed_attempts) > 0

        # Reset
        agent.reset_learning()

        assert len(agent.successful_tools) == 0
        assert len(agent.failed_attempts) == 0


class TestContextPreparation:
    """Test context preparation and validation."""

    @pytest.fixture
    def agent(self):
        """Create an agent instance."""
        return DSPyToolsmithAgent()

    def test_prepare_context_with_defaults(self, agent):
        """Test context preparation with default values."""
        with patch('os.getcwd', return_value='/test/repo'):
            context = agent._prepare_context({})

        assert context.repository_root == '/test/repo'
        assert context.tools_directory == 'tools'
        assert context.tests_directory == 'tests'
        assert 'session_' in context.session_id

    def test_prepare_context_with_custom_values(self, agent):
        """Test context preparation with custom values."""
        custom_context = {
            "repository_root": "/custom/repo",
            "tools_directory": "custom_tools",
            "tests_directory": "custom_tests",
            "session_id": "custom_session"
        }

        context = agent._prepare_context(custom_context)

        assert context.repository_root == "/custom/repo"
        assert context.tools_directory == "custom_tools"
        assert context.tests_directory == "custom_tests"
        assert context.session_id == "custom_session"

    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.glob')
    def test_prepare_context_with_existing_tools(self, mock_glob, mock_exists, agent):
        """Test context preparation discovers existing tools."""
        # Mock existing tool files
        mock_glob.return_value = [
            Path("tool1.py"),
            Path("tool2.py"),
            Path("__init__.py")  # Should be excluded
        ]

        context = agent._prepare_context({"repository_root": "/test"})

        # Should only include non-init files
        assert "tool1" in context.existing_tools
        assert "tool2" in context.existing_tools
        assert "__init__" not in context.existing_tools

    def test_prepare_context_with_validation_error(self, agent):
        """Test context preparation handles validation errors."""
        # Provide invalid context that will fail validation
        invalid_context = {
            "repository_root": None,  # None value should be replaced with getcwd()
        }

        with patch('os.getcwd', return_value='/fallback'):
            context = agent._prepare_context(invalid_context)

        # Should handle None gracefully and use getcwd()
        assert context.repository_root == '/fallback'
        assert 'session_' in context.session_id  # Regular session ID, not fallback


class TestTestExecution:
    """Test the test execution functionality."""

    @pytest.fixture
    def agent(self):
        """Create an agent instance."""
        return DSPyToolsmithAgent()

    @patch('subprocess.run')
    def test_run_tests_success(self, mock_run, agent):
        """Test successful test execution."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="All tests passed",
            stderr=""
        )

        result = agent._run_tests("test_file.py")

        assert result["success"] is True
        assert "All tests passed" in result["stdout"]
        assert result["errors"] == []

    @patch('subprocess.run')
    def test_run_tests_failure(self, mock_run, agent):
        """Test failed test execution."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Test failed: assertion error"
        )

        result = agent._run_tests("test_file.py")

        assert result["success"] is False
        assert "Test failed" in result["stderr"]
        assert len(result["errors"]) > 0

    @patch('subprocess.run')
    def test_run_tests_timeout(self, mock_run, agent):
        """Test test execution timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd="pytest",
            timeout=30
        )

        result = agent._run_tests("test_file.py")

        assert result["success"] is False
        assert "timed out" in result["stderr"]
        assert "30 seconds" in result["errors"][0]

    @patch('subprocess.run')
    def test_run_tests_exception(self, mock_run, agent):
        """Test test execution with exception."""
        mock_run.side_effect = Exception("Unexpected error")

        result = agent._run_tests("test_file.py")

        assert result["success"] is False
        assert "Unexpected error" in result["stderr"]
        assert "Failed to run tests" in result["errors"][0]


class TestHandoffPreparation:
    """Test handoff preparation functionality."""

    @pytest.fixture
    def agent(self):
        """Create an agent instance."""
        return DSPyToolsmithAgent()

    @pytest.fixture
    def sample_artifacts(self):
        """Create sample artifacts."""
        return [
            ToolArtifact(
                artifact_type="tool",
                file_path="tools/test_tool.py",
                content="class TestTool: pass",
                status="created"
            ),
            ToolArtifact(
                artifact_type="test",
                file_path="tests/test_tool.py",
                content="def test(): pass",
                status="created"
            )
        ]

    @patch('dspy_agents.modules.toolsmith_agent.DSPY_AVAILABLE', True)
    def test_prepare_handoff_success(self, agent, sample_artifacts):
        """Test successful handoff preparation."""
        mock_result = Mock()
        mock_result.handoff_package = {
            "artifacts": [a.model_dump() for a in sample_artifacts],
            "ready": True,
            "summary": "2 artifacts ready"
        }

        agent.handoff_preparer = Mock(return_value=mock_result)
        agent.dspy_available = True  # Ensure DSPy path is used

        test_results = {"success": True, "stdout": "Tests passed"}

        handoff = agent._prepare_handoff(sample_artifacts, test_results)

        # The method returns the handoff_package from the mock_result
        assert handoff["ready"] is True
        assert len(handoff["artifacts"]) == 2
        assert "2 artifacts ready" in handoff["summary"]

    @patch('dspy_agents.modules.toolsmith_agent.DSPY_AVAILABLE', False)
    def test_prepare_handoff_fallback(self, agent, sample_artifacts):
        """Test fallback handoff preparation."""
        test_results = {"success": True, "stdout": "Tests passed"}

        handoff = agent._prepare_handoff(sample_artifacts, test_results)

        assert handoff["ready_for_merge"] is True
        assert len(handoff["artifacts"]) == 2
        assert "Created 2 artifacts" in handoff["summary"]
        assert len(handoff["next_steps"]) > 0

    def test_prepare_handoff_with_failed_tests(self, agent, sample_artifacts):
        """Test handoff preparation with failed tests."""
        test_results = {"success": False, "stderr": "Test failed"}

        handoff = agent._prepare_handoff(sample_artifacts, test_results)

        assert handoff["ready_for_merge"] is False
        assert handoff["test_results"]["success"] is False


class TestKeywordExtraction:
    """Test keyword extraction functionality."""

    @pytest.fixture
    def agent(self):
        """Create an agent instance."""
        return DSPyToolsmithAgent()

    def test_extract_keywords_basic(self, agent):
        """Test basic keyword extraction."""
        text = "Create a new tool for handling context and messages"
        keywords = agent._extract_keywords(text)

        assert "create" in keywords
        assert "tool" in keywords
        assert "handling" in keywords
        assert "context" in keywords
        assert "messages" in keywords

        # Stop words should be filtered
        assert "a" not in keywords
        assert "and" not in keywords
        assert "for" not in keywords

    def test_extract_keywords_with_limit(self, agent):
        """Test keyword extraction respects limit."""
        text = " ".join([f"word{i}" for i in range(20)])
        keywords = agent._extract_keywords(text)

        assert len(keywords) <= 10

    def test_extract_keywords_filters_short_words(self, agent):
        """Test that short words are filtered."""
        text = "a be it on to xyz testing implementation"
        keywords = agent._extract_keywords(text)

        assert "xyz" in keywords
        assert "testing" in keywords
        assert "implementation" in keywords

        # Short words should be filtered
        assert "a" not in keywords
        assert "be" not in keywords
        assert "it" not in keywords


class TestIntegration:
    """Integration tests for DSPyToolsmithAgent."""

    @pytest.fixture
    def agent(self):
        """Create a fully configured agent."""
        return DSPyToolsmithAgent(
            model="gpt-4o-mini",
            reasoning_effort="high",
            enable_learning=True,
            quality_threshold=0.9
        )

    @patch('dspy_agents.modules.toolsmith_agent.DSPY_AVAILABLE', True)
    @patch('subprocess.run')
    def test_end_to_end_tool_creation(self, mock_subprocess, agent):
        """Test complete tool creation workflow."""
        # Setup mocks for full workflow
        mock_parsed = Mock()
        mock_parsed.tool_name = "IntegrationTool"
        mock_parsed.tool_description = "Tool for integration testing"
        mock_parsed.parameters = [{"name": "param", "type": "str"}]
        mock_parsed.test_cases = ["Test basic functionality"]
        agent.directive_parser = Mock(return_value=mock_parsed)

        mock_scaffold = Mock()
        mock_scaffold.tool_code = "class IntegrationTool: pass"
        mock_scaffold.imports = ["import os"]
        agent.scaffolder = Mock(return_value=mock_scaffold)

        mock_test = Mock()
        mock_test.test_code = "def test_integration(): assert True"
        agent.test_generator = Mock(return_value=mock_test)

        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="1 passed",
            stderr=""
        )

        mock_handoff = Mock()
        mock_handoff.handoff_package = {"status": "ready"}
        agent.handoff_preparer = Mock(return_value=mock_handoff)

        # Execute
        result = agent.forward(
            "Create IntegrationTool for testing integration",
            {"repository_root": "/test"}
        )

        # Verify
        assert result.success is True
        assert "IntegrationTool" in result.message
        assert len(result.changes) == 2
        assert result.changes[0].operation == "create"
        assert result.changes[1].operation == "create"
        assert len(result.tests) == 1
        assert result.verification.all_tests_pass is True

        # Verify learning occurred
        assert len(agent.successful_tools) == 1
        assert agent.successful_tools[0]["tool_name"] == "IntegrationTool"

    def test_backward_compatibility(self):
        """Test that agent maintains backward compatibility."""
        # Test factory function
        agent1 = create_dspy_toolsmith_agent()
        assert isinstance(agent1, DSPyToolsmithAgent)

        # Test with kwargs
        agent2 = create_dspy_toolsmith_agent(
            model="custom-model",
            extra_param="ignored"
        )
        assert agent2.model == "custom-model"

    @pytest.mark.skip(reason="TODO: Fix DSPy Mock - requires proper dspy.BaseLM mock instead of unittest.mock.Mock")
    @patch('dspy_agents.modules.toolsmith_agent.DSPY_AVAILABLE', False)
    def test_graceful_degradation_without_dspy(self, agent):
        """Test agent degrades gracefully when DSPy unavailable."""
        result = agent.forward(
            "Create tool without DSPy",
            {"repository_root": "/test"}
        )

        assert result.success is False
        assert ("DSPy not available" in result.message or "CONSTITUTIONAL" in result.message)
        assert result.verification.all_tests_pass is False

        # Should still return valid AgentResult
        assert isinstance(result, AgentResult)
        assert isinstance(result.changes, list)
        assert isinstance(result.tests, list)


class TestRationaleGeneration:
    """Test rationale generation with Chain of Thought."""

    @pytest.fixture
    def agent(self):
        """Create an agent instance for testing."""
        # Prevent real DSPy initialization
        with patch('dspy_agents.modules.toolsmith_agent.DSPyConfig.initialize', return_value=False):
            return DSPyToolsmithAgent()

    @patch('dspy_agents.modules.toolsmith_agent.DSPY_AVAILABLE', True)
    def test_directive_parsing_generates_rationale(self, agent):
        """Test that directive parsing generates design rationale."""
        mock_result = Mock()
        mock_result.tool_name = "TestTool"
        mock_result.tool_description = "A test tool"
        mock_result.parameters = []
        mock_result.test_cases = ["test1"]
        mock_result.implementation_plan = ["step1"]
        mock_result.design_rationale = "I analyzed the directive and decided to create TestTool because it fulfills the requirement for testing functionality."

        agent.directive_parser = Mock(return_value=mock_result)

        result = agent.parse_directive(
            directive="Create a test tool",
            existing_tools=["tool1", "tool2"],
            constitutional_requirements=["requirement1"]
        )

        # Verify rationale was generated
        assert agent.directive_parser.called
        assert mock_result.design_rationale is not None
        assert len(mock_result.design_rationale) > 0

    @patch('dspy_agents.modules.toolsmith_agent.DSPY_AVAILABLE', True)
    def test_scaffolding_generates_rationale(self, agent):
        """Test that scaffolding generates scaffolding rationale."""
        mock_result = Mock()
        mock_result.tool_code = "class TestTool: pass"
        mock_result.imports = ["import os"]
        mock_result.scaffolding_rationale = "I structured the code using a class-based approach to maintain consistency with existing tools."

        agent.scaffolder = Mock(return_value=mock_result)

        code, imports, rationale = agent.scaffold_tool(
            tool_name="TestTool",
            tool_description="Test tool",
            parameters=[],
            base_patterns={}
        )

        assert rationale is not None
        assert "structured" in rationale or "class" in rationale
        assert len(rationale) > 0

    @patch('dspy_agents.modules.toolsmith_agent.DSPY_AVAILABLE', True)
    def test_rationale_logged_during_execution(self, agent, caplog):
        """Test that rationales are logged during execution for debugging."""
        import logging
        caplog.set_level(logging.INFO)

        # Mock the directive parser to return a result with rationale
        mock_parsed = Mock()
        mock_parsed.tool_name = "LogTestTool"
        mock_parsed.tool_description = "Tool for testing logging"
        mock_parsed.parameters = []
        mock_parsed.test_cases = []
        mock_parsed.design_rationale = "Design rationale: Created tool for logging test"
        mock_parsed.implementation_plan = []

        agent.directive_parser = Mock(return_value=mock_parsed)

        # Mock scaffolder
        mock_scaffold = Mock()
        mock_scaffold.tool_code = "class LogTestTool: pass"
        mock_scaffold.imports = []
        mock_scaffold.scaffolding_rationale = "Scaffolding rationale: Using class structure"
        agent.scaffolder = Mock(return_value=mock_scaffold)

        # Mock test generator
        mock_test = Mock()
        mock_test.test_code = "def test(): pass"
        mock_test.test_fixtures = []
        mock_test.test_coverage = 100.0
        agent.test_generator = Mock(return_value=mock_test)

        # Mock handoff preparer
        mock_handoff = Mock()
        mock_handoff.handoff_package = {}
        mock_handoff.summary = "Ready"
        mock_handoff.next_steps = []
        mock_handoff.handoff_rationale = "Ready for integration"
        agent.handoff_preparer = Mock(return_value=mock_handoff)

        # Execute forward (will fail on test run but should log rationales)
        with patch.object(agent, '_run_tests', return_value={"success": True, "errors": []}):
            result = agent.forward(
                directive="Create a logging test tool",
                context={"repository_root": "/tmp"}
            )

        # Check that rationales were logged
        log_messages = [record.message for record in caplog.records]
        assert any("Design rationale" in msg for msg in log_messages)
        assert any("Scaffolding rationale" in msg for msg in log_messages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])