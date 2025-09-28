"""
Simple test suite for ChiefArchitectAgent to verify basic functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from chief_architect_agent import create_chief_architect_agent


class TestChiefArchitectAgentBasic:
    """Basic tests for ChiefArchitectAgent creation and configuration."""

    def test_agent_creation_succeeds(self):
        """Test that agent can be created without errors."""
        with patch('agency_swarm.Agent') as mock_agent_class:
            # Mock all dependencies to avoid complex setup
            with patch('chief_architect_agent.chief_architect_agent.create_agent_context') as mock_context:
                with patch('chief_architect_agent.chief_architect_agent.get_model_instance', return_value='gpt-5'):
                    with patch('chief_architect_agent.chief_architect_agent.create_model_settings', return_value=MagicMock()):
                        with patch('chief_architect_agent.chief_architect_agent.select_instructions_file', return_value='instructions.md'):
                            with patch('chief_architect_agent.chief_architect_agent.create_message_filter_hook', return_value=Mock()):
                                with patch('chief_architect_agent.chief_architect_agent.create_memory_integration_hook', return_value=Mock()):
                                    with patch('chief_architect_agent.chief_architect_agent.create_composite_hook', return_value=Mock()):
                                        # Setup mock context
                                        mock_ctx = Mock()
                                        mock_ctx.session_id = "test_session"
                                        mock_ctx.store_memory = Mock()
                                        mock_context.return_value = mock_ctx

                                        # Setup mock agent
                                        mock_agent = Mock()
                                        mock_agent_class.return_value = mock_agent

                                        # Create agent
                                        agent = create_chief_architect_agent()

                                        # Verify creation succeeded
                                        assert agent is not None
                                        assert mock_agent_class.called

    def test_agent_has_correct_name(self):
        """Test that agent is created with correct name."""
        with patch('agency_swarm.Agent') as mock_agent_class:
            with patch('chief_architect_agent.chief_architect_agent.create_agent_context'):
                with patch('chief_architect_agent.chief_architect_agent.get_model_instance', return_value='gpt-5'):
                    with patch('chief_architect_agent.chief_architect_agent.create_model_settings', return_value=MagicMock()):
                        with patch('chief_architect_agent.chief_architect_agent.select_instructions_file', return_value='instructions.md'):
                            # Create agent
                            create_chief_architect_agent()

                            # Check name was set correctly
                            call_kwargs = mock_agent_class.call_args[1]
                            assert call_kwargs['name'] == "ChiefArchitectAgent"

    def test_agent_description_includes_key_terms(self):
        """Test that agent description contains expected terms."""
        with patch('agency_swarm.Agent') as mock_agent_class:
            with patch('chief_architect_agent.chief_architect_agent.create_agent_context'):
                with patch('chief_architect_agent.chief_architect_agent.get_model_instance', return_value='gpt-5'):
                    with patch('chief_architect_agent.chief_architect_agent.create_model_settings', return_value=MagicMock()):
                        with patch('chief_architect_agent.chief_architect_agent.select_instructions_file', return_value='instructions.md'):
                            # Create agent
                            create_chief_architect_agent()

                            # Check description
                            call_kwargs = mock_agent_class.call_args[1]
                            description = call_kwargs['description']

                            # Verify key terms
                            assert "strategic leader" in description
                            assert "continuous improvement" in description
                            assert "[SELF-DIRECTED TASK]" in description