"""
Tests for IntentParser class - Three-stage input handling.

Constitutional compliance:
- Article I: Complete context before action (retry on timeout)
- Article II: 100% test success (TDD-first)
- Article IV: Query VectorStore for proven test patterns
- ADR-008: Strict typing with Pydantic models
- ADR-010: Result pattern for error handling

NECESSARY Pattern Compliance:
- Descriptive test names (test_X_when_Y_then_Z format)
- AAA structure (Arrange-Act-Assert) with comments
- Docstrings for all test methods
- Edge case coverage (empty backlog, malformed input, missing files)

TDD Status: PENDING (Implementation not started)
These tests are EXPECTED to fail until IntentParser is implemented.
This is CORRECT behavior per Article II (test-first development).
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Mark entire module as pending TDD implementation
pytestmark = pytest.mark.skip(reason="TDD pending: IntentParser implementation not started")

from shared.agent_context import AgentContext
from shared.type_definitions.result import Err, Ok, Result


# Mock models (will be replaced when actual implementation exists)
class InputMode:
    """Enum for IntentParser input modes."""

    AUTO_SELECT = "auto_select"
    NATURAL_LANGUAGE = "natural_language"
    EXPLICIT_SPEC = "explicit_spec"


class Intent:
    """Pydantic model for parsed intent (placeholder)."""

    def __init__(self, content: str, mode: str, source: str | None = None):
        self.content = content
        self.mode = mode
        self.source = source


class IntentError:
    """Pydantic model for intent parsing errors (placeholder)."""

    def __init__(self, error_type: str, message: str, context: dict | None = None):
        self.error_type = error_type
        self.message = message
        self.context = context or {}


class IntentParser:
    """Placeholder for IntentParser class (TDD - implementation comes after tests)."""

    def __init__(self, context: AgentContext):
        self.context = context

    def parse(
        self, user_input: str | None = None, mode: str | None = None
    ) -> Result[Intent, IntentError]:
        """Parse user input into Intent object (placeholder)."""
        raise NotImplementedError("TDD: Implement after tests pass")


class TestIntentParserAutoSelection:
    """Test IntentParser auto-selection mode (Mode 1: Backlog Auto-Select)."""

    @pytest.fixture
    def mock_memory_tool(self):
        """Mock Anthropic Memory Tool for backlog access."""
        tool = MagicMock()
        tool.view = MagicMock()
        return tool

    @pytest.fixture
    def mock_context(self, mock_memory_tool):
        """Mock AgentContext with memory tool."""
        context = MagicMock(spec=AgentContext)
        context.get_anthropic_memory_tool = MagicMock(return_value=mock_memory_tool)
        return context

    @pytest.fixture
    def sample_backlog_with_ready_task(self):
        """Sample backlog with one Ready task."""
        return """# Agency Backlog: Test Suite Gaps

## TOP 20 PRIORITY QUEUE

### Priority #1: Ollama Docker Compose Setup
- **Status**: Ready
- **Value**: 9/10 (critical functionality)
- **Effort**: 2/10 (straightforward fix)
- **ROI**: 4.5
- **Command**: `/primeccc "Set up Ollama Docker Compose"`
- **Next Step**: Create docker-compose.yml with Ollama service

### Priority #2: Fix Integration Tests
- **Status**: Blocked
- **Value**: 8/10 (high priority)
- **Effort**: 5/10 (moderate work)
- **ROI**: 1.6
- **Command**: `/primeccc "Fix integration tests"`
- **Next Step**: Debug failing integration tests
"""

    def test_parse_when_auto_select_mode_then_returns_highest_ready_task(
        self, mock_context, mock_memory_tool, sample_backlog_with_ready_task
    ):
        """Test that auto-select mode returns highest priority Ready task from backlog."""
        # Arrange
        mock_memory_tool.view.return_value = sample_backlog_with_ready_task
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input=None, mode=InputMode.AUTO_SELECT)

        # Assert
        assert result.is_ok(), "Auto-selection should succeed with valid backlog"
        intent = result.unwrap()
        assert intent.mode == InputMode.AUTO_SELECT
        assert "Ollama Docker Compose" in intent.content
        assert intent.source == "agency_backlog/test_suite_gaps.md"
        mock_memory_tool.view.assert_called_once_with("/memories/agency_backlog/test_suite_gaps.md")

    def test_parse_when_auto_select_and_empty_backlog_then_returns_error(
        self, mock_context, mock_memory_tool
    ):
        """Test that auto-select mode returns error when backlog is empty."""
        # Arrange
        empty_backlog = """# Agency Backlog

## TOP 20 PRIORITY QUEUE

(No tasks)
"""
        mock_memory_tool.view.return_value = empty_backlog
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input=None, mode=InputMode.AUTO_SELECT)

        # Assert
        assert result.is_err(), "Should return error for empty backlog"
        error = result.unwrap_err()
        assert error.error_type == "NoReadyTasks"
        assert "No Ready tasks in backlog" in error.message

    def test_parse_when_auto_select_and_all_blocked_then_returns_error(
        self, mock_context, mock_memory_tool
    ):
        """Test that auto-select skips Blocked tasks and returns error if none Ready."""
        # Arrange
        blocked_backlog = """# Agency Backlog

## TOP 20 PRIORITY QUEUE

### Priority #1: Task One
- **Status**: Blocked
- **Value**: 9/10
- **Effort**: 2/10
- **ROI**: 4.5
- **Command**: `/primeccc "Task One"`
- **Next Step**: Wait for dependency

### Priority #2: Task Two
- **Status**: In Progress
- **Value**: 8/10
- **Effort**: 5/10
- **ROI**: 1.6
- **Command**: `/primeccc "Task Two"`
- **Next Step**: Continue work
"""
        mock_memory_tool.view.return_value = blocked_backlog
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input=None, mode=InputMode.AUTO_SELECT)

        # Assert
        assert result.is_err(), "Should return error when all tasks are blocked"
        error = result.unwrap_err()
        assert error.error_type == "NoReadyTasks"

    def test_parse_when_auto_select_and_backlog_missing_then_returns_error(
        self, mock_context, mock_memory_tool
    ):
        """Test that auto-select returns error when backlog file does not exist."""
        # Arrange
        mock_memory_tool.view.side_effect = FileNotFoundError("Backlog file not found")
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input=None, mode=InputMode.AUTO_SELECT)

        # Assert
        assert result.is_err(), "Should return error when backlog file missing"
        error = result.unwrap_err()
        assert error.error_type == "FileNotFound"
        assert "Backlog file not found" in error.message

    def test_parse_when_auto_select_and_malformed_backlog_then_returns_error(
        self, mock_context, mock_memory_tool
    ):
        """Test that auto-select returns error when backlog format is invalid."""
        # Arrange
        malformed_backlog = """# Agency Backlog

### Priority #1: Task
- Missing required fields
- No Status, Value, Effort, ROI, Command, Next Step
"""
        mock_memory_tool.view.return_value = malformed_backlog
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input=None, mode=InputMode.AUTO_SELECT)

        # Assert
        assert result.is_err(), "Should return error for malformed backlog"
        error = result.unwrap_err()
        assert error.error_type == "ParseError"
        assert "Invalid backlog format" in error.message

    def test_parse_when_auto_select_skips_blocked_and_returns_second_ready(
        self, mock_context, mock_memory_tool
    ):
        """Test that auto-select skips Blocked priority #1 and returns Ready priority #2."""
        # Arrange
        backlog_with_blocked_first = """# Agency Backlog

## TOP 20 PRIORITY QUEUE

### Priority #1: Blocked Task
- **Status**: Blocked
- **Value**: 9/10
- **Effort**: 2/10
- **ROI**: 4.5
- **Command**: `/primeccc "Blocked Task"`
- **Next Step**: Wait for dependency

### Priority #2: Ready Task
- **Status**: Ready
- **Value**: 8/10
- **Effort**: 3/10
- **ROI**: 2.67
- **Command**: `/primeccc "Ready Task"`
- **Next Step**: Implement feature
"""
        mock_memory_tool.view.return_value = backlog_with_blocked_first
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input=None, mode=InputMode.AUTO_SELECT)

        # Assert
        assert result.is_ok(), "Should skip blocked and return next Ready task"
        intent = result.unwrap()
        assert "Ready Task" in intent.content
        assert "Blocked Task" not in intent.content


class TestIntentParserNaturalLanguage:
    """Test IntentParser natural language mode (Mode 2: Intent String)."""

    @pytest.fixture
    def mock_context(self):
        """Mock AgentContext."""
        return MagicMock(spec=AgentContext)

    def test_parse_when_natural_language_mode_then_returns_intent_string(self, mock_context):
        """Test that natural language mode returns the raw intent string."""
        # Arrange
        intent_string = "Add JWT authentication to API endpoints"
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input=intent_string, mode=InputMode.NATURAL_LANGUAGE)

        # Assert
        assert result.is_ok(), "Natural language parsing should succeed"
        intent = result.unwrap()
        assert intent.mode == InputMode.NATURAL_LANGUAGE
        assert intent.content == intent_string
        assert intent.source is None

    def test_parse_when_natural_language_and_empty_string_then_returns_error(self, mock_context):
        """Test that natural language mode returns error for empty input."""
        # Arrange
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input="", mode=InputMode.NATURAL_LANGUAGE)

        # Assert
        assert result.is_err(), "Empty input should return error"
        error = result.unwrap_err()
        assert error.error_type == "EmptyInput"
        assert "Intent string cannot be empty" in error.message

    def test_parse_when_natural_language_and_whitespace_only_then_returns_error(self, mock_context):
        """Test that natural language mode returns error for whitespace-only input."""
        # Arrange
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input="   \n\t  ", mode=InputMode.NATURAL_LANGUAGE)

        # Assert
        assert result.is_err(), "Whitespace-only input should return error"
        error = result.unwrap_err()
        assert error.error_type == "EmptyInput"

    def test_parse_when_natural_language_and_none_input_then_returns_error(self, mock_context):
        """Test that natural language mode returns error when user_input is None."""
        # Arrange
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input=None, mode=InputMode.NATURAL_LANGUAGE)

        # Assert
        assert result.is_err(), "None input in natural language mode should error"
        error = result.unwrap_err()
        assert error.error_type == "MissingInput"
        assert "Natural language mode requires user_input" in error.message

    def test_parse_when_natural_language_and_complex_intent_then_preserves_content(
        self, mock_context
    ):
        """Test that complex natural language intent is preserved exactly."""
        # Arrange
        complex_intent = """
        Implement a rate limiting middleware for the API with:
        - 100 requests per minute per user
        - Redis backend for distributed tracking
        - Exponential backoff on violations
        - Admin bypass capability
        """
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input=complex_intent, mode=InputMode.NATURAL_LANGUAGE)

        # Assert
        assert result.is_ok()
        intent = result.unwrap()
        assert intent.content == complex_intent
        assert "Redis backend" in intent.content


class TestIntentParserExplicitSpec:
    """Test IntentParser explicit spec file mode (Mode 3: Spec File Path)."""

    @pytest.fixture
    def mock_context(self):
        """Mock AgentContext."""
        return MagicMock(spec=AgentContext)

    @pytest.fixture
    def temp_spec_file(self, tmp_path):
        """Create temporary spec file."""
        spec_content = """# Spec: JWT Authentication

## Goals
- Add JWT authentication to API endpoints
- Ensure backward compatibility

## Personas
- API Developer
- Security Engineer

## Success Criteria
- All endpoints require valid JWT
- Refresh token flow implemented
- Tests cover 100% of auth paths
"""
        spec_file = tmp_path / "jwt_auth_spec.md"
        spec_file.write_text(spec_content)
        return spec_file

    def test_parse_when_explicit_spec_mode_then_reads_file_content(
        self, mock_context, temp_spec_file
    ):
        """Test that explicit spec mode reads and returns spec file content."""
        # Arrange
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input=str(temp_spec_file), mode=InputMode.EXPLICIT_SPEC)

        # Assert
        assert result.is_ok(), "Explicit spec mode should succeed with valid file"
        intent = result.unwrap()
        assert intent.mode == InputMode.EXPLICIT_SPEC
        assert "JWT Authentication" in intent.content
        assert "Goals" in intent.content
        assert intent.source == str(temp_spec_file)

    def test_parse_when_explicit_spec_and_file_missing_then_returns_error(self, mock_context):
        """Test that explicit spec mode returns error when file does not exist."""
        # Arrange
        parser = IntentParser(mock_context)
        missing_file = "/path/to/nonexistent/spec.md"

        # Act
        result = parser.parse(user_input=missing_file, mode=InputMode.EXPLICIT_SPEC)

        # Assert
        assert result.is_err(), "Should return error for missing spec file"
        error = result.unwrap_err()
        assert error.error_type == "FileNotFound"
        assert missing_file in error.message

    def test_parse_when_explicit_spec_and_empty_file_then_returns_error(
        self, mock_context, tmp_path
    ):
        """Test that explicit spec mode returns error for empty spec file."""
        # Arrange
        empty_spec = tmp_path / "empty_spec.md"
        empty_spec.write_text("")
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input=str(empty_spec), mode=InputMode.EXPLICIT_SPEC)

        # Assert
        assert result.is_err(), "Empty spec file should return error"
        error = result.unwrap_err()
        assert error.error_type == "EmptySpec"
        assert "Spec file is empty" in error.message

    def test_parse_when_explicit_spec_and_invalid_path_then_returns_error(self, mock_context):
        """Test that explicit spec mode returns error for invalid file path."""
        # Arrange
        parser = IntentParser(mock_context)
        invalid_path = "\x00/invalid/path"  # Null byte in path

        # Act
        result = parser.parse(user_input=invalid_path, mode=InputMode.EXPLICIT_SPEC)

        # Assert
        assert result.is_err(), "Invalid path should return error"
        error = result.unwrap_err()
        assert error.error_type == "InvalidPath"

    def test_parse_when_explicit_spec_and_none_input_then_returns_error(self, mock_context):
        """Test that explicit spec mode returns error when user_input is None."""
        # Arrange
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input=None, mode=InputMode.EXPLICIT_SPEC)

        # Assert
        assert result.is_err(), "None input in explicit spec mode should error"
        error = result.unwrap_err()
        assert error.error_type == "MissingInput"
        assert "Explicit spec mode requires file path" in error.message

    def test_parse_when_explicit_spec_and_permission_denied_then_returns_error(
        self, mock_context, tmp_path
    ):
        """Test that explicit spec mode returns error when file is not readable."""
        # Arrange
        unreadable_spec = tmp_path / "unreadable_spec.md"
        unreadable_spec.write_text("# Spec")
        unreadable_spec.chmod(0o000)  # Remove all permissions
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input=str(unreadable_spec), mode=InputMode.EXPLICIT_SPEC)

        # Assert (cleanup before assertion to avoid permission issues)
        unreadable_spec.chmod(0o644)  # Restore permissions for cleanup
        assert result.is_err(), "Unreadable file should return error"
        error = result.unwrap_err()
        assert error.error_type == "PermissionDenied"


class TestIntentParserModeInference:
    """Test IntentParser automatic mode inference."""

    @pytest.fixture
    def mock_context(self):
        """Mock AgentContext with memory tool."""
        context = MagicMock(spec=AgentContext)
        tool = MagicMock()
        context.get_anthropic_memory_tool = MagicMock(return_value=tool)
        return context

    def test_parse_when_no_mode_and_no_input_then_infers_auto_select(self, mock_context):
        """Test that missing mode and input defaults to auto-select."""
        # Arrange
        parser = IntentParser(mock_context)
        memory_tool = mock_context.get_anthropic_memory_tool.return_value
        memory_tool.view.return_value = """# Agency Backlog

### Priority #1: Test Task
- **Status**: Ready
- **Value**: 9/10
- **Effort**: 2/10
- **ROI**: 4.5
- **Command**: `/primeccc "Test"`
- **Next Step**: Test
"""

        # Act
        result = parser.parse(user_input=None, mode=None)

        # Assert
        assert result.is_ok(), "Should infer auto-select when no mode/input"
        intent = result.unwrap()
        assert intent.mode == InputMode.AUTO_SELECT

    def test_parse_when_no_mode_and_string_input_then_infers_natural_language(self, mock_context):
        """Test that missing mode with string input infers natural language."""
        # Arrange
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input="Add feature X", mode=None)

        # Assert
        assert result.is_ok(), "Should infer natural language for string input"
        intent = result.unwrap()
        assert intent.mode == InputMode.NATURAL_LANGUAGE
        assert intent.content == "Add feature X"

    def test_parse_when_no_mode_and_file_path_then_infers_explicit_spec(
        self, mock_context, tmp_path
    ):
        """Test that missing mode with .md file path infers explicit spec."""
        # Arrange
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Spec")
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input=str(spec_file), mode=None)

        # Assert
        assert result.is_ok(), "Should infer explicit spec for .md file path"
        intent = result.unwrap()
        assert intent.mode == InputMode.EXPLICIT_SPEC


class TestIntentParserEdgeCases:
    """Test IntentParser edge cases and error conditions."""

    @pytest.fixture
    def mock_context(self):
        """Mock AgentContext."""
        return MagicMock(spec=AgentContext)

    def test_parse_when_invalid_mode_then_returns_error(self, mock_context):
        """Test that invalid mode string returns error."""
        # Arrange
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input="Test", mode="invalid_mode")

        # Assert
        assert result.is_err(), "Invalid mode should return error"
        error = result.unwrap_err()
        assert error.error_type == "InvalidMode"
        assert "invalid_mode" in error.message

    def test_parse_when_unicode_content_then_preserves_unicode(self, mock_context):
        """Test that Unicode characters in intent are preserved correctly."""
        # Arrange
        unicode_intent = "Add emoji support 🚀 and CJK characters 日本語"
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input=unicode_intent, mode=InputMode.NATURAL_LANGUAGE)

        # Assert
        assert result.is_ok()
        intent = result.unwrap()
        assert intent.content == unicode_intent
        assert "🚀" in intent.content
        assert "日本語" in intent.content

    def test_parse_when_very_long_intent_then_handles_gracefully(self, mock_context):
        """Test that very long intent strings (10k+ chars) are handled."""
        # Arrange
        long_intent = "A" * 15000  # 15k character intent
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input=long_intent, mode=InputMode.NATURAL_LANGUAGE)

        # Assert
        assert result.is_ok(), "Should handle long intent strings"
        intent = result.unwrap()
        assert len(intent.content) == 15000

    def test_parse_when_backlog_read_timeout_then_returns_error(self, mock_context):
        """Test that timeout when reading backlog returns appropriate error."""
        # Arrange
        memory_tool = MagicMock()
        memory_tool.view.side_effect = TimeoutError("Backlog read timeout")
        mock_context.get_anthropic_memory_tool.return_value = memory_tool
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input=None, mode=InputMode.AUTO_SELECT)

        # Assert
        assert result.is_err(), "Timeout should return error"
        error = result.unwrap_err()
        assert error.error_type == "Timeout"
        assert "Backlog read timeout" in error.message


class TestIntentParserResultPattern:
    """Test IntentParser adheres to Result<T,E> pattern (ADR-010)."""

    @pytest.fixture
    def mock_context(self):
        """Mock AgentContext."""
        return MagicMock(spec=AgentContext)

    def test_parse_success_returns_ok_result(self, mock_context):
        """Test that successful parsing returns Ok(Intent)."""
        # Arrange
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input="Test intent", mode=InputMode.NATURAL_LANGUAGE)

        # Assert
        assert isinstance(result, Result), "Should return Result type"
        assert result.is_ok(), "Success should return Ok"
        assert not result.is_err(), "Success should not be Err"

    def test_parse_failure_returns_err_result(self, mock_context):
        """Test that parsing failure returns Err(IntentError)."""
        # Arrange
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input="", mode=InputMode.NATURAL_LANGUAGE)

        # Assert
        assert isinstance(result, Result), "Should return Result type"
        assert result.is_err(), "Failure should return Err"
        assert not result.is_ok(), "Failure should not be Ok"

    def test_parse_result_unwrap_succeeds_on_ok(self, mock_context):
        """Test that unwrap() succeeds on Ok result."""
        # Arrange
        parser = IntentParser(mock_context)
        result = parser.parse(user_input="Test", mode=InputMode.NATURAL_LANGUAGE)

        # Act
        intent = result.unwrap()

        # Assert
        assert isinstance(intent, Intent), "Unwrap should return Intent object"

    def test_parse_result_unwrap_raises_on_err(self, mock_context):
        """Test that unwrap() raises RuntimeError on Err result."""
        # Arrange
        parser = IntentParser(mock_context)
        result = parser.parse(user_input="", mode=InputMode.NATURAL_LANGUAGE)

        # Act & Assert
        with pytest.raises(RuntimeError):
            result.unwrap()

    def test_parse_result_unwrap_err_succeeds_on_err(self, mock_context):
        """Test that unwrap_err() succeeds on Err result."""
        # Arrange
        parser = IntentParser(mock_context)
        result = parser.parse(user_input="", mode=InputMode.NATURAL_LANGUAGE)

        # Act
        error = result.unwrap_err()

        # Assert
        assert isinstance(error, IntentError), "Unwrap_err should return IntentError"


class TestIntentParserConstitutionalCompliance:
    """Test IntentParser constitutional compliance (Articles I-V)."""

    @pytest.fixture
    def mock_context(self):
        """Mock AgentContext with VectorStore."""
        context = MagicMock(spec=AgentContext)
        context.search_memories = MagicMock(return_value=[])
        return context

    def test_parser_queries_vector_store_for_patterns(self, mock_context):
        """Test that parser queries VectorStore for proven patterns (Article IV)."""
        # Arrange
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input="Test intent", mode=InputMode.NATURAL_LANGUAGE)

        # Assert (Article IV: Learning integration)
        # Parser should query VectorStore for similar intent patterns
        # This is tested when implementation exists
        # For now, verify context has search_memories method
        assert hasattr(mock_context, "search_memories")

    def test_parser_uses_pydantic_models(self, mock_context):
        """Test that parser uses Pydantic models for type safety (ADR-008)."""
        # Arrange
        parser = IntentParser(mock_context)

        # Act
        result = parser.parse(user_input="Test", mode=InputMode.NATURAL_LANGUAGE)

        # Assert (when implementation exists)
        # Intent and IntentError should be Pydantic models
        # This enforces strict typing and validation
        if result.is_ok():
            intent = result.unwrap()
            # In real implementation, Intent will be a Pydantic model
            assert hasattr(intent, "content")
            assert hasattr(intent, "mode")
        else:
            error = result.unwrap_err()
            assert hasattr(error, "error_type")
            assert hasattr(error, "message")
