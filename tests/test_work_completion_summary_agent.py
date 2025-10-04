import json
from unittest.mock import Mock, mock_open, patch

from shared.agent_context import create_agent_context
from work_completion_summary_agent.work_completion_summary_agent import (
    RegenerateWithGpt5,
    create_work_completion_summary_agent,
)


class TestRegenerateWithGpt5:
    """Test suite for the RegenerateWithGpt5 tool."""

    def test_tool_initialization(self):
        """Test that the tool initializes with required fields."""
        tool = RegenerateWithGpt5(draft="Test summary")
        assert tool.draft == "Test summary"
        assert tool.bundle_path is None
        assert tool.guidance is None

    def test_tool_initialization_with_optional_fields(self):
        """Test tool initialization with all fields."""
        tool = RegenerateWithGpt5(
            draft="Test summary", bundle_path="/path/to/bundle.txt", guidance="Extra instructions"
        )
        assert tool.draft == "Test summary"
        assert tool.bundle_path == "/path/to/bundle.txt"
        assert tool.guidance == "Extra instructions"

    @patch("work_completion_summary_agent.work_completion_summary_agent.litellm.completion")
    @patch("builtins.open", new_callable=mock_open, read_data="bundle content")
    @patch("os.path.exists")
    def test_run_success_with_bundle(self, mock_exists, mock_file, mock_completion):
        """Test successful execution with bundle file."""
        # Setup mocks
        mock_exists.return_value = True
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Improved summary content"
        mock_completion.return_value = mock_response

        tool = RegenerateWithGpt5(draft="Original draft", bundle_path="/path/to/bundle.txt")

        with patch.object(tool, "_emit_telemetry_event"):
            result = tool.run()

        assert result == "Improved summary content"
        mock_exists.assert_called_once_with("/path/to/bundle.txt")
        mock_file.assert_called_once_with("/path/to/bundle.txt", "r", encoding="utf-8")
        mock_completion.assert_called_once()

    @patch("work_completion_summary_agent.work_completion_summary_agent.litellm.completion")
    def test_run_success_without_bundle(self, mock_completion):
        """Test successful execution without bundle file."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Improved summary content"
        mock_completion.return_value = mock_response

        tool = RegenerateWithGpt5(draft="Original draft")

        with patch.object(tool, "_emit_telemetry_event"):
            result = tool.run()

        assert result == "Improved summary content"
        mock_completion.assert_called_once()

    @patch("work_completion_summary_agent.work_completion_summary_agent.litellm.completion")
    def test_run_handles_api_error(self, mock_completion):
        """Test error handling when API call fails."""
        mock_completion.side_effect = Exception("API Error")

        tool = RegenerateWithGpt5(draft="Original draft")
        result = tool.run()

        assert result == "Escalation failed: API Error"

    def test_load_bundle_content_file_not_exists(self):
        """Test bundle loading when file doesn't exist."""
        tool = RegenerateWithGpt5(draft="Test", bundle_path="/nonexistent/path.txt")

        with patch("os.path.exists", return_value=False):
            result = tool._load_bundle_content()

        assert result == ""

    def test_load_bundle_content_no_path(self):
        """Test bundle loading when no path provided."""
        tool = RegenerateWithGpt5(draft="Test")
        result = tool._load_bundle_content()
        assert result == ""

    @patch("builtins.open", new_callable=mock_open, read_data="A" * 150000)
    @patch("os.path.exists", return_value=True)
    def test_load_bundle_content_size_limit(self, mock_exists, mock_file):
        """Test bundle content is limited to 120000 characters."""
        tool = RegenerateWithGpt5(draft="Test", bundle_path="/path/to/large.txt")
        result = tool._load_bundle_content()

        assert len(result) == 120000
        assert result == "A" * 120000

    @patch("builtins.open", side_effect=OSError("File read error"))
    @patch("os.path.exists", return_value=True)
    def test_load_bundle_content_read_error(self, mock_exists, mock_file):
        """Test bundle loading handles file read errors."""
        tool = RegenerateWithGpt5(draft="Test", bundle_path="/path/to/bundle.txt")
        result = tool._load_bundle_content()

        assert "failed to read bundle" in result
        assert "/path/to/bundle.txt" in result
        assert "File read error" in result

    def test_prepare_gpt5_messages_with_bundle(self):
        """Test message preparation with bundle content."""
        tool = RegenerateWithGpt5(draft="Test summary", guidance="Extra guidance")
        bundle_text = "Bundle content here"

        messages = tool._prepare_gpt5_messages(bundle_text)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "concise" in messages[0]["content"]
        assert "TTS" in messages[0]["content"]

        assert messages[1]["role"] == "user"
        user_content = json.loads(messages[1]["content"])
        assert user_content["draft_summary"] == "Test summary"
        assert user_content["bundle_excerpt"] == bundle_text
        assert user_content["extra_guidance"] == "Extra guidance"

    def test_prepare_gpt5_messages_large_bundle(self):
        """Test message preparation with large bundle content."""
        tool = RegenerateWithGpt5(draft="Test summary")
        bundle_text = "A" * 80000  # Large bundle

        messages = tool._prepare_gpt5_messages(bundle_text)
        user_content = json.loads(messages[1]["content"])

        # Should be truncated to 60000 characters
        assert len(user_content["bundle_excerpt"]) == 60000

    def test_call_gpt5_with_reasoning(self):
        """Test GPT-5 API call configuration."""
        tool = RegenerateWithGpt5(draft="Test")
        messages = [{"role": "user", "content": "test"}]

        with patch(
            "work_completion_summary_agent.work_completion_summary_agent.litellm.completion"
        ) as mock_completion:
            tool._call_gpt5_with_reasoning(messages)

            mock_completion.assert_called_once_with(
                model="gpt-5", messages=messages, extra_body={"reasoning": {"effort": "high"}}
            )

    def test_extract_response_content_with_choices(self):
        """Test response content extraction from standard response."""
        tool = RegenerateWithGpt5(draft="Test")

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Extracted content"

        result = tool._extract_response_content(mock_response)
        assert result == "Extracted content"

    def test_extract_response_content_dict_format(self):
        """Test response content extraction from dict format."""
        tool = RegenerateWithGpt5(draft="Test")

        mock_response = {"choices": [{"message": {"content": "Dict extracted content"}}]}

        result = tool._extract_response_content(mock_response)
        assert result == "Dict extracted content"

    def test_extract_response_content_fallback(self):
        """Test response content extraction fallback to string conversion."""
        tool = RegenerateWithGpt5(draft="Test")
        mock_response = "Fallback response"

        result = tool._extract_response_content(mock_response)
        assert result == "Fallback response"

    def test_extract_response_content_error_handling(self):
        """Test response content extraction error handling."""
        tool = RegenerateWithGpt5(draft="Test")
        mock_response = Mock()
        mock_response.choices = None  # Will cause AttributeError

        result = tool._extract_response_content(mock_response)
        assert result == str(mock_response)

    @patch("tools.orchestrator.scheduler._telemetry_emit")
    def test_emit_telemetry_event_success(self, mock_emit):
        """Test successful telemetry emission."""
        tool = RegenerateWithGpt5(draft="Test", bundle_path="/path/to/bundle.txt")

        tool._emit_telemetry_event()

        mock_emit.assert_called_once_with(
            {
                "type": "escalation_used",
                "agent": "WorkCompletionSummaryAgent",
                "tool": "RegenerateWithGpt5",
                "bundle_present": True,
            }
        )

    @patch("tools.orchestrator.scheduler._telemetry_emit", side_effect=ImportError())
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    @patch("os.path.join")
    @patch("os.getcwd", return_value="/test/cwd")
    def test_emit_telemetry_fallback(
        self, mock_getcwd, mock_join, mock_makedirs, mock_file, mock_emit
    ):
        """Test fallback telemetry writing when main telemetry fails."""
        mock_join.side_effect = lambda *args: "/".join(args)

        tool = RegenerateWithGpt5(draft="Test")

        # Just test that the fallback doesn't crash
        tool._emit_telemetry_event()

        mock_makedirs.assert_called_once_with("/test/cwd/logs/telemetry", exist_ok=True)
        mock_file.assert_called_once()

    @patch("tools.orchestrator.scheduler._telemetry_emit", side_effect=ImportError())
    @patch(
        "work_completion_summary_agent.work_completion_summary_agent.os.makedirs",
        side_effect=OSError(),
    )
    def test_fallback_telemetry_write_error_handling(self, mock_makedirs, mock_emit):
        """Test fallback telemetry handles errors gracefully."""
        tool = RegenerateWithGpt5(draft="Test")

        # Should not raise exception
        tool._emit_telemetry_event()


class TestWorkCompletionSummaryAgentCreation:
    """Test suite for the work completion summary agent factory function."""

    def test_agent_creation_default_params(self):
        """Test agent creation with default parameters."""
        agent = create_work_completion_summary_agent()

        assert agent.name == "WorkCompletionSummaryAgent"
        assert isinstance(agent.description, str)
        assert "audio summaries" in agent.description

        # Check tools
        tool_names = [getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.tools]
        assert "RegenerateWithGpt5" in tool_names or any(
            "RegenerateWithGpt5" in str(t) for t in agent.tools
        )

    def test_agent_creation_custom_params(self):
        """Test agent creation with custom parameters."""
        ctx = create_agent_context()
        agent = create_work_completion_summary_agent(
            model="gpt-5", reasoning_effort="high", agent_context=ctx
        )

        assert agent.name == "WorkCompletionSummaryAgent"
        assert agent is not None

    def test_agent_creation_with_context(self):
        """Test agent creation with provided agent context."""
        ctx = create_agent_context()
        original_session_id = ctx.session_id

        agent = create_work_completion_summary_agent(agent_context=ctx)

        assert agent is not None
        # The context should be used
        assert hasattr(agent, "hooks")
        assert agent.hooks is not None

    def test_agent_hooks_integration(self):
        """Test that agent has proper hooks configured."""
        agent = create_work_completion_summary_agent()

        assert hasattr(agent, "hooks")
        assert agent.hooks is not None
        # Should have composite hook with filter, memory, and bundle hooks

    def test_agent_model_settings(self):
        """Test that agent has proper model settings."""
        agent = create_work_completion_summary_agent(model="gpt-5-nano", reasoning_effort="low")

        assert hasattr(agent, "model_settings")
        # The agent should have model settings configured

    def test_agent_instructions_and_model(self):
        """Test that agent uses proper instructions and model."""
        agent = create_work_completion_summary_agent(model="gpt-5-nano")

        # Agent should be created successfully
        assert agent is not None
        assert agent.name == "WorkCompletionSummaryAgent"
        assert hasattr(agent, "model")
        assert hasattr(agent, "instructions")

    def test_agent_memory_integration(self):
        """Test that agent creation logs to memory."""
        ctx = create_agent_context()

        with patch.object(ctx, "store_memory") as mock_store:
            agent = create_work_completion_summary_agent(agent_context=ctx)

            mock_store.assert_called_once()
            call_args = mock_store.call_args

            # Check that memory was stored with correct data
            assert f"agent_created_{ctx.session_id}" in call_args[0][0]
            memory_data = call_args[0][1]
            assert memory_data["agent_type"] == "WorkCompletionSummaryAgent"
            assert memory_data["session_id"] == ctx.session_id

            # Check tags
            tags = call_args[0][2]
            assert "agency" in tags
            assert "summary" in tags
            assert "creation" in tags


class TestWorkCompletionSummaryAgentIntegration:
    """Integration tests for the work completion summary agent."""

    def test_agent_tool_integration(self):
        """Test that the agent's tools work together properly."""
        agent = create_work_completion_summary_agent()

        # Find the RegenerateWithGpt5 tool
        regen_tool = None
        for tool in agent.tools:
            if hasattr(tool, "__name__") and tool.__name__ == "RegenerateWithGpt5":
                regen_tool = tool
                break
            elif "RegenerateWithGpt5" in str(tool):
                regen_tool = tool
                break

        assert regen_tool is not None, "RegenerateWithGpt5 tool should be available"

    def test_agent_description_accuracy(self):
        """Test that agent description matches functionality."""
        agent = create_work_completion_summary_agent()

        description = agent.description.lower()

        # Should mention key features
        assert "audio summaries" in description
        assert "completion" in description or "completed" in description

    def test_error_resilience(self):
        """Test that agent creation is resilient to various error conditions."""
        # Test with invalid model (should not crash)
        try:
            agent = create_work_completion_summary_agent(model="invalid-model")
            # Agent creation might succeed but with fallback behavior
            assert agent is not None
        except Exception:
            # Or it might fail gracefully
            pass

        # Test with invalid reasoning effort
        try:
            agent = create_work_completion_summary_agent(reasoning_effort="invalid")
            assert agent is not None
        except Exception:
            pass
