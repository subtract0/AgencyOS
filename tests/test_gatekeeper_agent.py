"""
Test suite for Gatekeeper Agent (Class 14 Refactor).
"""

import pytest
from unittest.mock import MagicMock, patch
from cells.governor.gatekeeper import create_gatekeeper_agent
from shared.lean_agent import LeanAgent

class TestGatekeeperAgent:
    """Test Gatekeeper Agent functionality."""

    @patch("shared.lean_agent.OpenAI")
    def test_gatekeeper_initialization(self, mock_openai, monkeypatch):
        """Test that Gatekeeper initializes with correct settings."""
        # Arrange
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.delenv("OPENAI_API_BASE", raising=False)
        
        # Act
        agent = create_gatekeeper_agent(model="gpt-5", reasoning_effort="low")
        
        # Assert
        assert isinstance(agent, LeanAgent)
        assert agent.config.name == "Gatekeeper"
        # Description is not stored in AgentConfig in LeanAgent implementation
        # Verify instructions loaded
        assert len(agent.messages) > 0
        assert agent.messages[0].role == "system"
        # Verify model settings
        assert agent.config.model == "gpt-5"
        
    @patch("shared.lean_agent.OpenAI")
    def test_gatekeeper_run(self, mock_openai, monkeypatch):
        """Test basic run loop (mocked)."""
        # Arrange
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.delenv("OPENAI_API_BASE", raising=False)
        agent = create_gatekeeper_agent()
        
        mock_response = MagicMock()
        mock_response.content = "Opening the gate."
        mock_response.tool_calls = None
        mock_openai.return_value.chat.completions.create.return_value.choices = [
            MagicMock(message=mock_response)
        ]
        
        # Act
        result = agent.run("Hello")
        
        # Assert
        assert result == "Opening the gate."
