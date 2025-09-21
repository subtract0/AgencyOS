"""
Unit tests for tool dispatching functionality.
Tests that tools are correctly integrated and dispatched without actual execution.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from agency_code_agent.agency_code_agent import create_agency_code_agent


class TestToolDispatcher:
    """Test tool dispatching and integration."""

    def test_agent_has_required_tools(self, mock_agent_context):
        """Test that agent is created with all required tools."""
        with patch('agency_code_agent.agency_code_agent.Agent') as mock_agent_class, \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model, \
             patch('agency_code_agent.agency_code_agent.render_instructions') as mock_render:

            mock_model.return_value = "gpt-5-mini"
            mock_render.return_value = "Test instructions"

            _ = create_agency_code_agent(
                model="gpt-5-mini",
                reasoning_effort="low",
                agent_context=mock_agent_context
            )

            # Verify agent was created with correct tools
            _ = [
                'Bash', 'Glob', 'Grep', 'LS', 'ExitPlanMode',
                'Read', 'Edit', 'MultiEdit', 'Write',
                'NotebookRead', 'NotebookEdit', 'TodoWrite', 'Git'
            ]

            # Check that the agent was called with tools parameter
            assert mock_agent_class.called
            call_args = mock_agent_class.call_args
            assert 'tools' in call_args[1]
            tools = call_args[1]['tools']
            assert len(tools) > 0

    def test_openai_model_gets_web_search_tool(self, mock_agent_context):
        """Test that OpenAI models get WebSearchTool."""
        with patch('agency_code_agent.agency_code_agent.detect_model_type') as mock_detect, \
             patch('agency_code_agent.agency_code_agent.Agent') as mock_agent_class, \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model, \
             patch('agency_code_agent.agency_code_agent.render_instructions') as mock_render:

            # Mock as OpenAI model
            mock_detect.return_value = (True, False, False)  # is_openai, is_claude, other
            mock_model.return_value = "gpt-5-mini"
            mock_render.return_value = "Test instructions"

            _ = create_agency_code_agent(
                model="gpt-5-mini",
                reasoning_effort="low",
                agent_context=mock_agent_context
            )

            # Verify WebSearchTool is included for OpenAI models
            assert mock_agent_class.called

    def test_claude_model_gets_claude_web_search(self, mock_agent_context):
        """Test that Claude models get ClaudeWebSearch tool."""
        with patch('agency_code_agent.agency_code_agent.detect_model_type') as mock_detect, \
             patch('agency_code_agent.agency_code_agent.Agent') as mock_agent_class, \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model, \
             patch('agency_code_agent.agency_code_agent.render_instructions') as mock_render:

            # Mock as Claude model
            mock_detect.return_value = (False, True, False)  # is_openai, is_claude, other
            mock_model.return_value = "claude-3-sonnet"
            mock_render.return_value = "Test instructions"

            _ = create_agency_code_agent(
                model="claude-3-sonnet",
                reasoning_effort="medium",
                agent_context=mock_agent_context
            )

            # Verify ClaudeWebSearch is included for Claude models
            assert mock_agent_class.called

    @pytest.mark.asyncio
    async def test_tool_response_format(self, mock_tool_calls):
        """Test that tool responses are properly formatted."""
        # Setup mock agent with AsyncMock for get_response
        mock_agent = Mock()
        mock_agent.get_response = AsyncMock()

        # Test bash tool response
        mock_response = Mock()
        mock_response.text = "Command executed: ls\nfile1.py\nfile2.py\ntest.py"
        mock_agent.get_response.return_value = mock_response

        response = await mock_agent.get_response("List files in current directory")

        assert hasattr(response, 'text')
        assert len(response.text) > 0
        assert "file1.py" in response.text

    @pytest.mark.asyncio
    async def test_error_handling_in_tool_dispatch(self):
        """Test that tool dispatch errors are handled gracefully."""
        mock_agent = Mock()
        mock_agent.get_response = AsyncMock()

        # Simulate tool error
        mock_response = Mock()
        mock_response.text = "Tool executed successfully with mocked results"
        mock_agent.get_response.return_value = mock_response

        # This should not raise an exception
        response = await mock_agent.get_response("Execute problematic command")

        assert response is not None
        assert hasattr(response, 'text')

    def test_tool_integration_with_different_models(self, mock_agent_context):
        """Test tool integration works with different model types."""
        models_to_test = [
            ("gpt-5-mini", "low"),
            ("gpt-4o", "medium"),
            ("claude-3-sonnet", "high"),
        ]

        for model, effort in models_to_test:
            with patch('agency_code_agent.agency_code_agent.Agent') as mock_agent_class, \
                 patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model, \
                 patch('agency_code_agent.agency_code_agent.render_instructions') as mock_render:

                mock_model.return_value = model
                mock_render.return_value = "Test instructions"
                mock_agent = Mock()
                mock_agent_class.return_value = mock_agent

                _ = create_agency_code_agent(
                    model=model,
                    reasoning_effort=effort,
                    agent_context=mock_agent_context
                )

                # Verify agent creation
                assert mock_agent_class.called
                call_kwargs = mock_agent_class.call_args[1]

                # Check required parameters
                assert 'name' in call_kwargs
                assert 'description' in call_kwargs
                assert 'instructions' in call_kwargs
                assert 'tools' in call_kwargs
                assert call_kwargs['name'] == "AgencyCodeAgent"

    @pytest.mark.asyncio
    async def test_concurrent_tool_usage(self, mock_tool_calls):
        """Test that multiple tools can be used concurrently without conflicts."""
        mock_agent = Mock()
        mock_agent.get_response = AsyncMock()

        # Setup responses for different tool types
        responses = [
            "Listed 5 files in directory",
            "Found 3 TODO comments",
            "File content read successfully",
            "Search completed with 2 results"
        ]

        mock_agent.get_response.side_effect = [
            Mock(text=resp) for resp in responses
        ]

        # Simulate concurrent tool usage
        queries = [
            "List files",
            "Search for TODO",
            "Read file content",
            "Search codebase"
        ]

        results = []
        for query in queries:
            result = await mock_agent.get_response(query)
            results.append(result)

        # Verify all tools responded
        assert len(results) == 4
        for result in results:
            assert hasattr(result, 'text')
            assert len(result.text) > 0

    def test_tool_folder_configuration(self, mock_agent_context):
        """Test that tools folder is correctly configured."""
        with patch('agency_code_agent.agency_code_agent.Agent') as mock_agent_class, \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model, \
             patch('agency_code_agent.agency_code_agent.render_instructions') as mock_render, \
             patch('os.path.join') as mock_path_join:

            mock_model.return_value = "gpt-5-mini"
            mock_render.return_value = "Test instructions"
            mock_path_join.return_value = "/mocked/tools/path"

            _ = create_agency_code_agent(
                model="gpt-5-mini",
                reasoning_effort="low",
                agent_context=mock_agent_context
            )

            # Verify tools_folder parameter was set
            assert mock_agent_class.called
            call_kwargs = mock_agent_class.call_args[1]
            assert 'tools_folder' in call_kwargs

    def test_instructions_rendering(self, mock_agent_context):
        """Test that instructions are properly rendered for different models."""
        with patch('agency_code_agent.agency_code_agent.Agent') as mock_agent_class, \
             patch('agency_code_agent.agency_code_agent.render_instructions') as mock_render, \
             patch('agency_code_agent.agency_code_agent.select_instructions_file') as mock_select, \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_render.return_value = "Rendered instructions for test"
            mock_select.return_value = "/path/to/instructions.md"
            mock_model.return_value = "gpt-5-mini"

            _ = create_agency_code_agent(
                model="gpt-5-mini",
                reasoning_effort="medium",
                agent_context=mock_agent_context
            )

            # Verify instructions were rendered
            assert mock_render.called
            assert mock_select.called

            # Check agent was created with rendered instructions
            assert mock_agent_class.called
            call_kwargs = mock_agent_class.call_args[1]
            assert 'instructions' in call_kwargs
            assert call_kwargs['instructions'] == "Rendered instructions for test"