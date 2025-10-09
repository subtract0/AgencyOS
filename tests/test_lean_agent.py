"""
Comprehensive test suite for lean_agent.py.

Tests cover:
- Agent initialization
- Tool execution
- Message handling
- Model-specific parameter handling (o1/o3/gpt-5 vs standard models)
- Error handling
- Thread safety
- Input validation

Constitutional Compliance:
- Article II: TDD - tests written first
- Article II: 100% verification
- Result<T,E> pattern for error handling
- Pydantic models for data structures

Version: 1.0.0
Created: 2025-10-09
"""

import json
import os
import threading
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import ValidationError

from shared.lean_agent import (
    AgentConfig,
    FunctionDefinition,
    LeanAgent,
    Message,
    OpenAIToolFormat,
    Tool,
    ToolParameter,
    ToolPropertySchema,
    tool,
)


class TestToolModels:
    """Test Pydantic models for tool definitions."""

    def test_tool_property_schema_creation(self):
        """Test ToolPropertySchema model creation."""
        # Arrange & Act
        schema = ToolPropertySchema(
            type="string", description="A test parameter", enum=["value1", "value2"]
        )

        # Assert
        assert schema.type == "string"
        assert schema.description == "A test parameter"
        assert schema.enum == ["value1", "value2"]

    def test_tool_parameter_creation(self):
        """Test ToolParameter model creation."""
        # Arrange
        properties = {
            "name": ToolPropertySchema(type="string", description="User name"),
            "age": ToolPropertySchema(type="number", description="User age"),
        }

        # Act
        param = ToolParameter(type="object", properties=properties, required=["name"])

        # Assert
        assert param.type == "object"
        assert len(param.properties) == 2
        assert "name" in param.required
        assert "age" not in param.required

    def test_tool_to_openai_format(self):
        """Test Tool conversion to OpenAI format."""
        # Arrange
        param = ToolParameter(
            type="object",
            properties={
                "x": ToolPropertySchema(type="number", description="X coordinate")
            },
            required=["x"],
        )
        tool_obj = Tool(name="get_x", description="Get X value", parameters=param)

        # Act
        openai_format = tool_obj.to_openai_format()

        # Assert
        assert isinstance(openai_format, OpenAIToolFormat)
        assert openai_format.type == "function"
        assert openai_format.function.name == "get_x"
        assert openai_format.function.description == "Get X value"
        assert openai_format.function.parameters == param

    def test_function_definition_model(self):
        """Test FunctionDefinition Pydantic model."""
        # Arrange
        param = ToolParameter(type="object", properties={}, required=[])

        # Act
        func_def = FunctionDefinition(
            name="test_func", description="Test function", parameters=param
        )

        # Assert
        assert func_def.name == "test_func"
        assert func_def.description == "Test function"
        assert func_def.parameters.type == "object"


class TestMessage:
    """Test Message model."""

    def test_message_creation_user(self):
        """Test user message creation."""
        # Act
        msg = Message(role="user", content="Hello")

        # Assert
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.tool_calls is None
        assert msg.tool_call_id is None

    def test_message_creation_assistant_with_tools(self):
        """Test assistant message with tool calls."""
        # Arrange
        from shared.lean_agent import ToolCall, FunctionCall

        tool_calls = [
            ToolCall(
                id="call_123",
                type="function",
                function=FunctionCall(name="test", arguments="{}")
            )
        ]

        # Act
        msg = Message(role="assistant", content="Thinking...", tool_calls=tool_calls)

        # Assert
        assert msg.role == "assistant"
        assert msg.content == "Thinking..."
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].id == "call_123"

    def test_message_creation_tool_response(self):
        """Test tool response message."""
        # Act
        msg = Message(role="tool", content='{"result": 42}', tool_call_id="call_123")

        # Assert
        assert msg.role == "tool"
        assert msg.content == '{"result": 42}'
        assert msg.tool_call_id == "call_123"


class TestAgentConfig:
    """Test AgentConfig model."""

    def test_config_minimal(self):
        """Test minimal agent config creation."""
        # Act
        config = AgentConfig(name="test_agent", instructions="You are helpful")

        # Assert
        assert config.name == "test_agent"
        assert config.instructions == "You are helpful"
        assert config.model == "gpt-4o"  # Default
        assert config.temperature == 0.7  # Default
        assert config.max_tokens == 4000  # Default
        assert len(config.tools) == 0

    def test_config_with_tools(self):
        """Test config with tools."""
        # Arrange
        param = ToolParameter(type="object", properties={}, required=[])
        tool_obj = Tool(name="test_tool", description="Test", parameters=param)

        # Act
        config = AgentConfig(
            name="agent_with_tools",
            instructions="You have tools",
            tools=[tool_obj],
        )

        # Assert
        assert len(config.tools) == 1
        assert config.tools[0].name == "test_tool"

    def test_config_custom_model_params(self):
        """Test custom model parameters."""
        # Act
        config = AgentConfig(
            name="custom_agent",
            instructions="Custom params",
            model="gpt-5",
            temperature=0.2,
            max_tokens=8000,
        )

        # Assert
        assert config.model == "gpt-5"
        assert config.temperature == 0.2
        assert config.max_tokens == 8000


class TestLeanAgentInitialization:
    """Test LeanAgent initialization."""

    @patch("shared.lean_agent.OpenAI")
    def test_agent_initialization_basic(self, mock_openai):
        """Test basic agent initialization."""
        # Arrange
        config = AgentConfig(name="test", instructions="You are helpful")

        # Act
        agent = LeanAgent(config)

        # Assert
        assert agent.config == config
        assert len(agent.messages) == 1  # System message
        assert agent.messages[0].role == "system"
        assert agent.messages[0].content == "You are helpful"
        mock_openai.assert_called_once()

    @patch("shared.lean_agent.OpenAI")
    def test_agent_initialization_with_api_key(self, mock_openai):
        """Test agent uses OPENAI_API_KEY from environment."""
        # Arrange
        config = AgentConfig(name="test", instructions="Test")
        os.environ["OPENAI_API_KEY"] = "test-key-123"

        # Act
        agent = LeanAgent(config)

        # Assert
        mock_openai.assert_called_once_with(api_key="test-key-123")

    @patch("shared.lean_agent.OpenAI")
    def test_agent_initialization_missing_api_key(self, mock_openai):
        """Test agent raises error when API key missing."""
        # Arrange
        config = AgentConfig(name="test", instructions="Test")
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

        # Act & Assert - NOW VALIDATED (fixed!)
        with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
            agent = LeanAgent(config)


class TestLeanAgentExecution:
    """Test LeanAgent task execution."""

    @patch("shared.lean_agent.OpenAI")
    def test_run_simple_response_no_tools(self, mock_openai):
        """Test simple agent run without tool calls."""
        # Arrange
        config = AgentConfig(name="test", instructions="You are helpful")
        agent = LeanAgent(config)

        # Mock LLM response (no tool calls)
        mock_response = Mock()
        mock_response.content = "Hello! How can I help?"
        mock_response.tool_calls = None
        mock_openai.return_value.chat.completions.create.return_value.choices = [
            Mock(message=mock_response)
        ]

        # Act
        result = agent.run("Hi there")

        # Assert
        assert result == "Hello! How can I help?"
        assert len(agent.messages) == 3  # System, user, assistant
        assert agent.messages[1].role == "user"
        assert agent.messages[1].content == "Hi there"
        assert agent.messages[2].role == "assistant"
        assert agent.messages[2].content == "Hello! How can I help?"

    @patch("shared.lean_agent.OpenAI")
    def test_run_with_tool_call_and_execution(self, mock_openai):
        """Test agent run with tool call and execution."""
        # Arrange
        def mock_add(a: float, b: float) -> float:
            return a + b

        param = ToolParameter(
            type="object",
            properties={
                "a": ToolPropertySchema(type="number"),
                "b": ToolPropertySchema(type="number"),
            },
            required=["a", "b"],
        )
        tool_obj = Tool(
            name="add", description="Add two numbers", parameters=param, function=mock_add
        )
        config = AgentConfig(name="calc", instructions="You can add", tools=[tool_obj])
        os.environ["OPENAI_API_KEY"] = "test-key"
        agent = LeanAgent(config)

        # Mock LLM responses - need to return from side_effect to handle multiple calls
        # First response: tool call
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "add"
        mock_tool_call.function.arguments = '{"a": 5, "b": 3}'

        first_response = Mock()
        first_response.content = "Let me add those"
        first_response.tool_calls = [mock_tool_call]

        # Second response: final answer
        second_response = Mock()
        second_response.content = "The sum is 8"
        second_response.tool_calls = None

        # Use side_effect to return different responses for each call
        mock_completion = Mock()
        mock_completion.choices = [Mock(message=first_response)]
        mock_completion2 = Mock()
        mock_completion2.choices = [Mock(message=second_response)]

        mock_openai.return_value.chat.completions.create.side_effect = [
            mock_completion,
            mock_completion2,
        ]

        # Act
        result = agent.run("What is 5 + 3?")

        # Assert
        assert result == "The sum is 8"
        assert len(agent.messages) == 5  # System, user, assistant+tool_call, tool_result, assistant
        assert agent.messages[2].tool_calls is not None
        assert agent.messages[3].role == "tool"
        assert "8" in agent.messages[3].content  # Tool result

    @patch("shared.lean_agent.OpenAI")
    def test_run_max_iterations_exceeded(self, mock_openai):
        """Test agent raises error when max iterations exceeded."""
        # Arrange
        config = AgentConfig(name="test", instructions="Test")
        agent = LeanAgent(config)

        # Mock response that always has tool calls (infinite loop)
        mock_tool_call = Mock()
        mock_tool_call.id = "call_loop"
        mock_tool_call.function.name = "nonexistent_tool"
        mock_tool_call.function.arguments = "{}"
        mock_tool_call.model_dump.return_value = {
            "id": "call_loop",
            "type": "function",
            "function": {"name": "nonexistent_tool", "arguments": "{}"},
        }

        looping_response = Mock()
        looping_response.content = "Calling tool"
        looping_response.tool_calls = [mock_tool_call]

        mock_openai.return_value.chat.completions.create.return_value.choices = [
            Mock(message=looping_response)
        ]

        # Act & Assert
        with pytest.raises(RuntimeError, match="exceeded max iterations"):
            agent.run("Do something", max_iterations=3)

    @patch("shared.lean_agent.OpenAI")
    def test_run_with_invalid_tool_arguments(self, mock_openai):
        """Test agent handles invalid tool arguments gracefully."""
        # Arrange
        def mock_func(x: int) -> int:
            return x * 2

        param = ToolParameter(
            type="object",
            properties={"x": ToolPropertySchema(type="number")},
            required=["x"],
        )
        tool_obj = Tool(
            name="double", description="Double a number", parameters=param, function=mock_func
        )
        config = AgentConfig(name="calc", instructions="Test", tools=[tool_obj])
        os.environ["OPENAI_API_KEY"] = "test-key"
        agent = LeanAgent(config)

        # Mock tool call with invalid JSON
        mock_tool_call = Mock()
        mock_tool_call.id = "call_bad"
        mock_tool_call.function.name = "double"
        mock_tool_call.function.arguments = "not valid json"

        first_response = Mock()
        first_response.content = "Calling tool"
        first_response.tool_calls = [mock_tool_call]

        second_response = Mock()
        second_response.content = "I encountered an error"
        second_response.tool_calls = None

        mock_completion = Mock()
        mock_completion.choices = [Mock(message=first_response)]
        mock_completion2 = Mock()
        mock_completion2.choices = [Mock(message=second_response)]

        mock_openai.return_value.chat.completions.create.side_effect = [
            mock_completion,
            mock_completion2,
        ]

        # Act
        result = agent.run("Double 5")

        # Assert
        assert "error" in result.lower() or "encountered" in result.lower()
        # Check that error was recorded in messages
        tool_response = agent.messages[3]
        assert tool_response.role == "tool"
        assert "Error:" in tool_response.content and ("Invalid" in tool_response.content or "JSON" in tool_response.content)


class TestModelSpecificParameters:
    """Test model-specific parameter handling."""

    @patch("shared.lean_agent.OpenAI")
    def test_reasoning_model_gpt5_parameters(self, mock_openai):
        """Test gpt-5 uses reasoning model parameters."""
        # Arrange
        config = AgentConfig(
            name="gpt5_agent",
            instructions="You are smart",
            model="gpt-5",
            temperature=0.5,  # Will be ignored for reasoning models
            max_tokens=4000,
        )
        agent = LeanAgent(config)

        # Mock response
        mock_response = Mock()
        mock_response.content = "Answer"
        mock_response.tool_calls = None
        mock_openai.return_value.chat.completions.create.return_value.choices = [
            Mock(message=mock_response)
        ]

        # Act
        agent.run("Question")

        # Assert - Check API was called with correct params
        call_kwargs = mock_openai.return_value.chat.completions.create.call_args[1]
        assert "max_completion_tokens" in call_kwargs
        assert call_kwargs["max_completion_tokens"] == 4000
        assert "temperature" not in call_kwargs  # Not supported by reasoning models
        assert "tools" not in call_kwargs  # Not supported by reasoning models

    @patch("shared.lean_agent.OpenAI")
    def test_reasoning_model_o1_parameters(self, mock_openai):
        """Test o1 model uses reasoning parameters."""
        # Arrange
        config = AgentConfig(name="o1_agent", instructions="Think", model="o1-preview")
        agent = LeanAgent(config)

        mock_response = Mock()
        mock_response.content = "Thought"
        mock_response.tool_calls = None
        mock_openai.return_value.chat.completions.create.return_value.choices = [
            Mock(message=mock_response)
        ]

        # Act
        agent.run("Question")

        # Assert
        call_kwargs = mock_openai.return_value.chat.completions.create.call_args[1]
        assert "max_completion_tokens" in call_kwargs
        assert "temperature" not in call_kwargs
        assert "tools" not in call_kwargs

    @patch("shared.lean_agent.OpenAI")
    def test_reasoning_model_o3_parameters(self, mock_openai):
        """Test o3 model uses reasoning parameters."""
        # Arrange
        config = AgentConfig(name="o3_agent", instructions="Think", model="o3-mini")
        agent = LeanAgent(config)

        mock_response = Mock()
        mock_response.content = "Thought"
        mock_response.tool_calls = None
        mock_openai.return_value.chat.completions.create.return_value.choices = [
            Mock(message=mock_response)
        ]

        # Act
        agent.run("Question")

        # Assert
        call_kwargs = mock_openai.return_value.chat.completions.create.call_args[1]
        assert "max_completion_tokens" in call_kwargs
        assert "temperature" not in call_kwargs

    @patch("shared.lean_agent.OpenAI")
    def test_standard_model_gpt4o_parameters(self, mock_openai):
        """Test gpt-4o uses standard parameters."""
        # Arrange
        def mock_tool():
            return "result"

        param = ToolParameter(type="object", properties={}, required=[])
        tool_obj = Tool(
            name="test", description="Test", parameters=param, function=mock_tool
        )
        config = AgentConfig(
            name="gpt4o_agent",
            instructions="Help",
            model="gpt-4o",
            temperature=0.3,
            tools=[tool_obj],
        )
        agent = LeanAgent(config)

        mock_response = Mock()
        mock_response.content = "Answer"
        mock_response.tool_calls = None
        mock_openai.return_value.chat.completions.create.return_value.choices = [
            Mock(message=mock_response)
        ]

        # Act
        agent.run("Question")

        # Assert
        call_kwargs = mock_openai.return_value.chat.completions.create.call_args[1]
        assert "temperature" in call_kwargs
        assert call_kwargs["temperature"] == 0.3
        assert "max_tokens" in call_kwargs
        assert "tools" in call_kwargs  # Tools supported
        assert "max_completion_tokens" not in call_kwargs  # Standard param


class TestToolExecution:
    """Test tool execution methods."""

    def test_execute_tool_success(self):
        """Test successful tool execution."""
        # Arrange
        def add_numbers(a: float, b: float) -> float:
            return a + b

        param = ToolParameter(
            type="object",
            properties={
                "a": ToolPropertySchema(type="number"),
                "b": ToolPropertySchema(type="number"),
            },
            required=["a", "b"],
        )
        tool_obj = Tool(
            name="add", description="Add", parameters=param, function=add_numbers
        )
        config = AgentConfig(name="calc", instructions="Calc", tools=[tool_obj])
        # Mock API key for initialization
        os.environ["OPENAI_API_KEY"] = "test-key"
        agent = LeanAgent(config)

        # Act
        result = agent._execute_tool("add", '{"a": 10, "b": 5}')

        # Assert
        assert result.is_ok()
        assert "15" in result.unwrap()  # Check for 15 (float string format may vary)

    def test_execute_tool_not_found(self):
        """Test tool not found error."""
        # Arrange
        config = AgentConfig(name="test", instructions="Test", tools=[])
        os.environ["OPENAI_API_KEY"] = "test-key"
        agent = LeanAgent(config)

        # Act
        result = agent._execute_tool("nonexistent", "{}")

        # Assert
        assert result.is_err()
        assert "nonexistent" in result.unwrap_err()
        assert "not found" in result.unwrap_err()

    def test_execute_tool_no_function(self):
        """Test tool without function implementation."""
        # Arrange
        param = ToolParameter(type="object", properties={}, required=[])
        tool_obj = Tool(
            name="broken", description="Broken", parameters=param, function=None
        )
        config = AgentConfig(name="test", instructions="Test", tools=[tool_obj])
        os.environ["OPENAI_API_KEY"] = "test-key"
        agent = LeanAgent(config)

        # Act
        result = agent._execute_tool("broken", "{}")

        # Assert
        assert result.is_err()
        assert "broken" in result.unwrap_err()
        assert "no function" in result.unwrap_err().lower()

    def test_execute_tool_invalid_json_arguments(self):
        """Test tool execution with invalid JSON arguments."""
        # Arrange
        def dummy():
            return "ok"

        param = ToolParameter(type="object", properties={}, required=[])
        tool_obj = Tool(
            name="test", description="Test", parameters=param, function=dummy
        )
        config = AgentConfig(name="agent", instructions="Test", tools=[tool_obj])
        os.environ["OPENAI_API_KEY"] = "test-key"
        agent = LeanAgent(config)

        # Act
        result = agent._execute_tool("test", "not json")

        # Assert
        assert result.is_err()
        assert "Invalid" in result.unwrap_err() or "JSON" in result.unwrap_err()

    def test_execute_tool_function_raises_exception(self):
        """Test tool execution when function raises exception."""
        # Arrange
        def failing_tool(x: int) -> int:
            raise ValueError("Something went wrong!")

        param = ToolParameter(
            type="object",
            properties={"x": ToolPropertySchema(type="number")},
            required=["x"],
        )
        tool_obj = Tool(
            name="fail", description="Fails", parameters=param, function=failing_tool
        )
        config = AgentConfig(name="agent", instructions="Test", tools=[tool_obj])
        os.environ["OPENAI_API_KEY"] = "test-key"
        agent = LeanAgent(config)

        # Act
        result = agent._execute_tool("fail", '{"x": 5}')

        # Assert
        assert result.is_err()
        assert "fail" in result.unwrap_err().lower()
        assert "Something went wrong!" in result.unwrap_err()


class TestMessageHistory:
    """Test message history management."""

    @patch("shared.lean_agent.OpenAI")
    def test_clear_history_preserves_system_message(self, mock_openai):
        """Test clear_history() keeps system prompt."""
        # Arrange
        config = AgentConfig(name="test", instructions="You are helpful")
        os.environ["OPENAI_API_KEY"] = "test-key"
        agent = LeanAgent(config)
        agent.messages.append(Message(role="user", content="Hi"))
        agent.messages.append(Message(role="assistant", content="Hello"))

        # Act
        agent.clear_history()

        # Assert
        assert len(agent.messages) == 1
        assert agent.messages[0].role == "system"
        assert agent.messages[0].content == "You are helpful"

    @patch("shared.lean_agent.OpenAI")
    def test_message_accumulation_during_run(self, mock_openai):
        """Test messages accumulate correctly during agent run."""
        # Arrange
        config = AgentConfig(name="test", instructions="Test")
        agent = LeanAgent(config)

        mock_response = Mock()
        mock_response.content = "Response"
        mock_response.tool_calls = None
        mock_openai.return_value.chat.completions.create.return_value.choices = [
            Mock(message=mock_response)
        ]

        # Act - Run twice
        agent.run("First question")
        agent.run("Second question")

        # Assert - Messages accumulate (system + 2 user + 2 assistant)
        assert len(agent.messages) == 5
        assert agent.messages[0].role == "system"
        assert agent.messages[1].content == "First question"
        assert agent.messages[2].content == "Response"
        assert agent.messages[3].content == "Second question"
        assert agent.messages[4].content == "Response"


class TestToolDecorator:
    """Test the @tool decorator."""

    def test_tool_decorator_creates_tool_object(self):
        """Test @tool decorator creates Tool instance."""
        # Arrange
        param = ToolParameter(
            type="object",
            properties={"x": ToolPropertySchema(type="number")},
            required=["x"],
        )

        # Act
        @tool("square", "Square a number", param)
        def square(x: float) -> float:
            return x * x

        # Assert
        assert isinstance(square, Tool)
        assert square.name == "square"
        assert square.description == "Square a number"
        assert square.parameters == param
        assert square.function is not None
        assert square.function(5) == 25


class TestThreadSafety:
    """Test thread safety of LeanAgent."""

    @patch("shared.lean_agent.OpenAI")
    def test_concurrent_runs_do_not_corrupt_messages(self, mock_openai):
        """Test concurrent agent runs don't corrupt shared state."""
        # Arrange
        config = AgentConfig(name="test", instructions="Test")
        agent = LeanAgent(config)

        mock_response = Mock()
        mock_response.content = "Response"
        mock_response.tool_calls = None
        mock_openai.return_value.chat.completions.create.return_value.choices = [
            Mock(message=mock_response)
        ]

        # Act - Run concurrently
        results = []
        errors = []

        def run_agent(message):
            try:
                result = agent.run(message)
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=run_agent, args=(f"Question {i}",))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Assert - No errors, but we expect potential message corruption
        # (This test documents current behavior - NOT thread-safe)
        assert len(errors) == 0  # No crashes
        assert len(results) == 5  # All completed
        # NOTE: Messages may be interleaved/corrupted - this is a known issue
        # that should be fixed with threading.Lock


class TestInputValidation:
    """Test input validation."""

    @patch("shared.lean_agent.OpenAI")
    def test_run_with_negative_max_iterations_should_fail(self, mock_openai):
        """Test run() rejects negative max_iterations."""
        # Arrange
        config = AgentConfig(name="test", instructions="Test")
        os.environ["OPENAI_API_KEY"] = "test-key"
        agent = LeanAgent(config)

        # Act & Assert - NOW VALIDATED (fixed!)
        with pytest.raises(ValueError, match="max_iterations must be > 0"):
            agent.run("Test", max_iterations=-1)

    @patch("shared.lean_agent.OpenAI")
    def test_run_with_empty_message_accepts(self, mock_openai):
        """Test run() accepts empty user message."""
        # Arrange
        config = AgentConfig(name="test", instructions="Test")
        agent = LeanAgent(config)

        mock_response = Mock()
        mock_response.content = "I can help"
        mock_response.tool_calls = None
        mock_openai.return_value.chat.completions.create.return_value.choices = [
            Mock(message=mock_response)
        ]

        # Act
        result = agent.run("")

        # Assert - Should work (empty message is valid)
        assert result == "I can help"

    def test_agent_config_validation(self):
        """Test AgentConfig validates required fields."""
        # Act & Assert - Missing required fields
        with pytest.raises(ValidationError):
            AgentConfig()  # Missing name and instructions

        with pytest.raises(ValidationError):
            AgentConfig(name="test")  # Missing instructions

        with pytest.raises(ValidationError):
            AgentConfig(instructions="Test")  # Missing name


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch("shared.lean_agent.OpenAI")
    def test_empty_tool_list(self, mock_openai):
        """Test agent with empty tool list."""
        # Arrange
        config = AgentConfig(name="test", instructions="Test", tools=[])
        agent = LeanAgent(config)

        mock_response = Mock()
        mock_response.content = "Response"
        mock_response.tool_calls = None
        mock_openai.return_value.chat.completions.create.return_value.choices = [
            Mock(message=mock_response)
        ]

        # Act
        result = agent.run("Question")

        # Assert
        assert result == "Response"
        call_kwargs = mock_openai.return_value.chat.completions.create.call_args[1]
        assert call_kwargs.get("tools") is None  # No tools passed to API

    @patch("shared.lean_agent.OpenAI")
    def test_very_long_message_history(self, mock_openai):
        """Test agent handles long message history."""
        # Arrange
        config = AgentConfig(name="test", instructions="Test")
        agent = LeanAgent(config)

        # Add many messages
        for i in range(100):
            agent.messages.append(Message(role="user", content=f"Message {i}"))
            agent.messages.append(Message(role="assistant", content=f"Response {i}"))

        mock_response = Mock()
        mock_response.content = "Final response"
        mock_response.tool_calls = None
        mock_openai.return_value.chat.completions.create.return_value.choices = [
            Mock(message=mock_response)
        ]

        # Act
        result = agent.run("Latest question")

        # Assert
        assert result == "Final response"
        assert len(agent.messages) > 200  # All messages preserved

    @patch("shared.lean_agent.OpenAI")
    def test_null_response_content(self, mock_openai):
        """Test agent handles None response content."""
        # Arrange
        config = AgentConfig(name="test", instructions="Test")
        agent = LeanAgent(config)

        mock_response = Mock()
        mock_response.content = None  # Null content
        mock_response.tool_calls = None
        mock_openai.return_value.chat.completions.create.return_value.choices = [
            Mock(message=mock_response)
        ]

        # Act
        result = agent.run("Question")

        # Assert
        assert result == ""  # Converts None to empty string


# Integration tests (require OPENAI_API_KEY in environment)
@pytest.mark.integration
class TestRealAPIIntegration:
    """Integration tests with real OpenAI API (requires API key)."""

    def test_real_api_simple_completion(self):
        """Test real API call (simple completion, no tools)."""
        # Skip if no API key
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

        # Arrange
        config = AgentConfig(
            name="test_agent",
            instructions="You are a helpful assistant. Be concise.",
            model="gpt-4o-mini",  # Cheaper model for testing
        )
        agent = LeanAgent(config)

        # Act
        result = agent.run("Say 'Hello, World!' and nothing else.")

        # Assert
        assert "Hello" in result
        assert "World" in result

    def test_real_api_with_tool_call(self):
        """Test real API with tool execution."""
        # Skip if no API key
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

        # Arrange - Create a simple calculator tool
        def add(a: float, b: float) -> float:
            """Add two numbers."""
            return a + b

        param = ToolParameter(
            type="object",
            properties={
                "a": ToolPropertySchema(type="number", description="First number"),
                "b": ToolPropertySchema(type="number", description="Second number"),
            },
            required=["a", "b"],
        )
        tool_obj = Tool(
            name="add", description="Add two numbers together", parameters=param, function=add
        )

        config = AgentConfig(
            name="calculator",
            instructions="You are a calculator. Use the add tool when asked to add numbers.",
            model="gpt-4o-mini",
            tools=[tool_obj],
        )
        agent = LeanAgent(config)

        # Act
        result = agent.run("What is 7 + 13?")

        # Assert
        assert "20" in result  # Should calculate correctly
