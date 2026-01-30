
import pytest
from unittest.mock import MagicMock, patch
from cells.maintenance.medic_agent import create_medic_agent, run_tests_tool
from shared.lean_agent import LeanAgent

class TestMedicAgent:
    """Test Medic Agent functionality."""

    @patch("shared.lean_agent.OpenAI")
    @patch("cells.maintenance.medic_agent.ToolRegistry")
    def test_medic_initialization(self, mock_registry_cls, mock_openai, monkeypatch):
        """Test that Medic Agent initializes with correct tools."""
        # Arrange
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.delenv("OPENAI_API_BASE", raising=False)
        
        # Mock instance and scan_and_register
        mock_instance = MagicMock()
        mock_instance.scan_and_register.return_value = []
        mock_registry_cls.return_value = mock_instance
        
        # Act
        agent = create_medic_agent()
        
        # Assert
        assert isinstance(agent, LeanAgent)
        assert agent.config.name == "Medic"
        # Check that run_tests_tool is in the tools list
        tool_names = [t.name for t in agent.config.tools]
        assert "run_tests" in tool_names

    @patch("subprocess.run")
    def test_run_tests_tool(self, mock_subprocess):
        """Test the run_tests tool wrapper."""
        # Arrange
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Test passed"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        # Act
        result = run_tests_tool.function(test_path="tests/test_foo.py", fast=True)
        
        # Assert
        assert "✅ Tests Passed" in result
        mock_subprocess.assert_called_once()
        cmd = mock_subprocess.call_args[0][0]
        assert "run_tests.py" in cmd
        assert "--fast" in cmd
        assert "tests/test_foo.py" in cmd

    @patch("subprocess.run")
    def test_run_tests_tool_failure(self, mock_subprocess):
        """Test run_tests failure reporting."""
        # Arrange
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Test failed"
        mock_result.stderr = "Error details"
        mock_subprocess.return_value = mock_result
        
        # Act
        result = run_tests_tool.function(fast=True)
        
        # Assert
        assert "❌ Tests Failed" in result
        assert "Error details" in result
