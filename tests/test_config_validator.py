"""
Test suite for Configuration File Validator.

Tests YAML/JSON parsing, Pydantic validation, Result pattern error handling,
and AAA pattern compliance.

Constitutional Compliance:
- Article I: Complete context (test all functionality)
- Article II: 100% verification (all tests must pass)
- Article IV: Apply learnings from VectorStore (AAA pattern, pytest patterns)
- Article V: Trace to spec (verify all acceptance criteria)

NECESSARY Framework Coverage:
- N: Normal operation (valid YAML/JSON configs)
- E: Edge cases (empty files, unicode, boundary values)
- C: Corner cases (malformed syntax combinations)
- E: Error conditions (all ConfigErrorType variants)
- S: Security (file path validation, encoding)
- S: Stress (large file performance - future)
- A: Accessibility (API usability)
- R: Regression (ensure fixes don't break)
- Y: Yield (output validation - Result pattern)
"""

import json
import tempfile
from pathlib import Path

import pytest

from shared.config_validator import (
    AgencyConfig,
    AgentConfig,
    ConfigError,
    ConfigErrorType,
    MemoryConfig,
    parse_config_file,
    validate_config,
)


class TestValidConfigParsing:
    """Test normal operation (NECESSARY: N - Normal)."""

    def test_parse_valid_yaml_config_returns_ok_result(self):
        """Test parsing valid YAML configuration with all fields."""
        # Arrange
        config_content = """
planner:
  model: gpt-5
  temperature: 0.7
  max_tokens: 4000

coder:
  model: gpt-5
  temperature: 0.3
  max_tokens: 8000

memory:
  use_enhanced_memory: true
  vector_store_path: ~/.agency/vector_store
  session_id: demo_session

log_level: INFO
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert
            assert result.is_ok(), f"Expected Ok, got Err: {result.unwrap_err()}"
            config = result.unwrap()
            assert isinstance(config, AgencyConfig)
            assert config.planner.model == "gpt-5"
            assert config.planner.temperature == 0.7
            assert config.planner.max_tokens == 4000
            assert config.coder.model == "gpt-5"
            assert config.coder.temperature == 0.3
            assert config.coder.max_tokens == 8000
            assert config.memory.use_enhanced_memory is True
            assert config.memory.vector_store_path == "~/.agency/vector_store"
            assert config.memory.session_id == "demo_session"
            assert config.log_level == "INFO"
        finally:
            Path(temp_path).unlink()

    def test_parse_valid_json_config_returns_ok_result(self):
        """Test parsing valid JSON configuration."""
        # Arrange
        config_content = {
            "planner": {"model": "gpt-4o", "temperature": 0.5, "max_tokens": 2000},
            "coder": {"model": "gpt-5", "temperature": 0.2, "max_tokens": 6000},
            "memory": {
                "use_enhanced_memory": False,
                "vector_store_path": "/tmp/vector_store",
            },
            "log_level": "DEBUG",
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(config_content, f)
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert
            assert result.is_ok()
            config = result.unwrap()
            assert config.planner.model == "gpt-4o"
            assert config.coder.model == "gpt-5"
            assert config.memory.use_enhanced_memory is False
            assert config.log_level == "DEBUG"
        finally:
            Path(temp_path).unlink()

    def test_parse_yaml_with_default_values(self):
        """Test YAML parsing with optional fields using defaults."""
        # Arrange
        config_content = """
planner:
  model: gpt-5

coder:
  model: gpt-5

memory:
  vector_store_path: /path/to/store
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert
            assert result.is_ok()
            config = result.unwrap()
            # Check defaults
            assert config.planner.temperature == 0.7  # Default
            assert config.planner.max_tokens == 4000  # Default
            assert config.memory.use_enhanced_memory is True  # Default
            assert config.memory.session_id is None  # Default None
            assert config.log_level == "INFO"  # Default
        finally:
            Path(temp_path).unlink()

    def test_parse_json_with_null_session_id(self):
        """Test JSON parsing with explicit null for optional field."""
        # Arrange
        config_content = {
            "planner": {"model": "gpt-5"},
            "coder": {"model": "gpt-5"},
            "memory": {"vector_store_path": "/path", "session_id": None},
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(config_content, f)
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert
            assert result.is_ok()
            config = result.unwrap()
            assert config.memory.session_id is None
        finally:
            Path(temp_path).unlink()


class TestEdgeCases:
    """Test edge cases (NECESSARY: E - Edge cases)."""

    def test_empty_yaml_file_returns_validation_error(self):
        """Test parsing empty YAML file."""
        # Arrange
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write("")
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert
            assert result.is_err()
            error = result.unwrap_err()
            assert error.error_type == ConfigErrorType.SYNTAX_ERROR
        finally:
            Path(temp_path).unlink()

    def test_yaml_with_only_whitespace_returns_error(self):
        """Test YAML file with only whitespace."""
        # Arrange
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write("   \n\n   \t\n")
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert
            assert result.is_err()
            error = result.unwrap_err()
            assert error.error_type == ConfigErrorType.SYNTAX_ERROR
        finally:
            Path(temp_path).unlink()

    def test_yaml_with_unicode_characters(self):
        """Test YAML parsing with unicode characters."""
        # Arrange
        config_content = """
planner:
  model: gpt-5-日本語
  temperature: 0.7

coder:
  model: gpt-5

memory:
  vector_store_path: /path/to/ユニコード/store
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert
            assert result.is_ok()
            config = result.unwrap()
            assert "日本語" in config.planner.model
            assert "ユニコード" in config.memory.vector_store_path
        finally:
            Path(temp_path).unlink()

    def test_json_with_unicode_escapes(self):
        """Test JSON parsing with unicode escape sequences."""
        # Arrange
        config_content = {
            "planner": {"model": "gpt-5-\u65e5\u672c\u8a9e"},
            "coder": {"model": "gpt-5"},
            "memory": {"vector_store_path": "/path/\u30e6\u30cb\u30b3\u30fc\u30c9"},
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(config_content, f, ensure_ascii=False)
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert
            assert result.is_ok()
            config = result.unwrap()
            assert "日本語" in config.planner.model
        finally:
            Path(temp_path).unlink()

    def test_temperature_boundary_values(self):
        """Test temperature field boundary validation (0.0 to 2.0)."""
        # Arrange - Min boundary
        config_min = {
            "planner": {"model": "gpt-5", "temperature": 0.0},
            "coder": {"model": "gpt-5"},
            "memory": {"vector_store_path": "/path"},
        }

        # Act
        result_min = validate_config(config_min)

        # Assert - Min should be valid
        assert result_min.is_ok()
        assert result_min.unwrap().planner.temperature == 0.0

        # Arrange - Max boundary
        config_max = {
            "planner": {"model": "gpt-5", "temperature": 2.0},
            "coder": {"model": "gpt-5"},
            "memory": {"vector_store_path": "/path"},
        }

        # Act
        result_max = validate_config(config_max)

        # Assert - Max should be valid
        assert result_max.is_ok()
        assert result_max.unwrap().planner.temperature == 2.0

    def test_max_tokens_boundary_validation(self):
        """Test max_tokens must be greater than 0."""
        # Arrange - Invalid (0)
        config_zero = {
            "planner": {"model": "gpt-5", "max_tokens": 0},
            "coder": {"model": "gpt-5"},
            "memory": {"vector_store_path": "/path"},
        }

        # Act
        result_zero = validate_config(config_zero)

        # Assert - Should fail
        assert result_zero.is_err()
        error = result_zero.unwrap_err()
        assert error.error_type == ConfigErrorType.VALIDATION_ERROR
        assert "max_tokens" in error.field_path

        # Arrange - Valid (1)
        config_one = {
            "planner": {"model": "gpt-5", "max_tokens": 1},
            "coder": {"model": "gpt-5"},
            "memory": {"vector_store_path": "/path"},
        }

        # Act
        result_one = validate_config(config_one)

        # Assert - Should succeed
        assert result_one.is_ok()


class TestMalformedSyntax:
    """Test corner cases (NECESSARY: C - Corner cases)."""

    def test_malformed_yaml_unclosed_quote(self):
        """Test YAML with unclosed quote."""
        # Arrange
        config_content = """
planner:
  model: "gpt-5
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert
            assert result.is_err()
            error = result.unwrap_err()
            assert error.error_type == ConfigErrorType.SYNTAX_ERROR
            assert error.line_number is not None
        finally:
            Path(temp_path).unlink()

    def test_malformed_yaml_invalid_indentation(self):
        """Test YAML with invalid indentation."""
        # Arrange
        config_content = """
planner:
model: gpt-5
  temperature: 0.7
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert
            assert result.is_err()
            error = result.unwrap_err()
            assert error.error_type == ConfigErrorType.SYNTAX_ERROR
        finally:
            Path(temp_path).unlink()

    def test_malformed_json_trailing_comma(self):
        """Test JSON with trailing comma."""
        # Arrange
        json_content = """{
  "planner": {
    "model": "gpt-5",
  },
  "coder": {
    "model": "gpt-5"
  },
  "memory": {
    "vector_store_path": "/path"
  }
}"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(json_content)
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert
            assert result.is_err()
            error = result.unwrap_err()
            assert error.error_type == ConfigErrorType.SYNTAX_ERROR
            assert error.line_number is not None
            assert "comma" in error.suggestion.lower() or "bracket" in error.suggestion.lower()
        finally:
            Path(temp_path).unlink()

    def test_malformed_json_missing_bracket(self):
        """Test JSON with missing closing bracket."""
        # Arrange
        json_content = """{
  "planner": {
    "model": "gpt-5"
  },
  "coder": {
    "model": "gpt-5"
  },
  "memory": {
    "vector_store_path": "/path"

"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(json_content)
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert
            assert result.is_err()
            error = result.unwrap_err()
            assert error.error_type == ConfigErrorType.SYNTAX_ERROR
        finally:
            Path(temp_path).unlink()

    def test_yaml_root_is_list_not_dict(self):
        """Test YAML where root is list instead of dict."""
        # Arrange
        config_content = """
- planner:
    model: gpt-5
- coder:
    model: gpt-5
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert
            assert result.is_err()
            error = result.unwrap_err()
            assert error.error_type == ConfigErrorType.SYNTAX_ERROR
            assert "object" in error.message.lower()
            assert "list" in error.message.lower()
        finally:
            Path(temp_path).unlink()

    def test_json_root_is_array_not_object(self):
        """Test JSON where root is array instead of object."""
        # Arrange
        json_content = '[{"planner": {"model": "gpt-5"}}]'
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(json_content)
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert
            assert result.is_err()
            error = result.unwrap_err()
            assert error.error_type == ConfigErrorType.SYNTAX_ERROR
            assert "object" in error.message.lower()
        finally:
            Path(temp_path).unlink()


class TestErrorConditions:
    """Test error conditions (NECESSARY: E - Error conditions)."""

    def test_file_not_found_returns_error(self):
        """Test parsing non-existent file."""
        # Arrange
        nonexistent_path = "/tmp/nonexistent_config_12345.yaml"

        # Act
        result = parse_config_file(nonexistent_path)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert error.error_type == ConfigErrorType.FILE_NOT_FOUND
        assert nonexistent_path in error.message
        assert "check file path" in error.suggestion.lower()

    def test_unsupported_file_format_returns_error(self):
        """Test unsupported file extension."""
        # Arrange
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("some content")
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert
            assert result.is_err()
            error = result.unwrap_err()
            assert error.error_type == ConfigErrorType.UNSUPPORTED_FORMAT
            assert ".txt" in error.message
            assert ".yaml" in error.suggestion or ".json" in error.suggestion
        finally:
            Path(temp_path).unlink()

    def test_missing_required_field_returns_error(self):
        """Test configuration missing required field."""
        # Arrange
        config_data = {
            "planner": {
                # Missing required 'model' field
                "temperature": 0.7
            },
            "coder": {"model": "gpt-5"},
            "memory": {"vector_store_path": "/path"},
        }

        # Act
        result = validate_config(config_data)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert error.error_type == ConfigErrorType.MISSING_FIELD
        assert "model" in error.field_path
        assert "planner" in error.field_path
        assert "required" in error.message.lower() or "missing" in error.message.lower()
        assert error.suggestion is not None
        assert "add" in error.suggestion.lower()

    def test_type_coercion_string_to_number(self):
        """Test Pydantic type coercion (string to number) - this succeeds by design."""
        # Arrange - Pydantic v2 coerces compatible string types by default
        config_data = {
            "planner": {"model": "gpt-5", "temperature": "0.7"},  # String coerced to float
            "coder": {"model": "gpt-5"},
            "memory": {"vector_store_path": "/path"},
        }

        # Act
        result = validate_config(config_data)

        # Assert - Pydantic successfully coerces string "0.7" to float 0.7
        assert result.is_ok()
        config = result.unwrap()
        assert config.planner.temperature == 0.7
        assert isinstance(config.planner.temperature, float)

    def test_type_mismatch_number_instead_of_string(self):
        """Test type mismatch error (number instead of string)."""
        # Arrange
        config_data = {
            "planner": {"model": 5},  # Should be string
            "coder": {"model": "gpt-5"},
            "memory": {"vector_store_path": "/path"},
        }

        # Act
        result = validate_config(config_data)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert error.error_type == ConfigErrorType.VALIDATION_ERROR
        assert "model" in error.field_path

    def test_invalid_log_level_literal(self):
        """Test invalid log level (not in Literal options)."""
        # Arrange
        config_data = {
            "planner": {"model": "gpt-5"},
            "coder": {"model": "gpt-5"},
            "memory": {"vector_store_path": "/path"},
            "log_level": "TRACE",  # Not in ["DEBUG", "INFO", "WARNING", "ERROR"]
        }

        # Act
        result = validate_config(config_data)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert error.error_type == ConfigErrorType.VALIDATION_ERROR
        assert "log_level" in error.field_path

    def test_temperature_out_of_range_below_min(self):
        """Test temperature below minimum (0.0)."""
        # Arrange
        config_data = {
            "planner": {"model": "gpt-5", "temperature": -0.1},
            "coder": {"model": "gpt-5"},
            "memory": {"vector_store_path": "/path"},
        }

        # Act
        result = validate_config(config_data)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert error.error_type == ConfigErrorType.VALIDATION_ERROR
        assert "temperature" in error.field_path

    def test_temperature_out_of_range_above_max(self):
        """Test temperature above maximum (2.0)."""
        # Arrange
        config_data = {
            "planner": {"model": "gpt-5", "temperature": 2.1},
            "coder": {"model": "gpt-5"},
            "memory": {"vector_store_path": "/path"},
        }

        # Act
        result = validate_config(config_data)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert error.error_type == ConfigErrorType.VALIDATION_ERROR
        assert "temperature" in error.field_path

    def test_extra_fields_are_ignored_by_default(self):
        """Test extra fields are ignored (Pydantic v2 default behavior)."""
        # Arrange - Pydantic v2 ignores extra fields by default (not an error)
        config_data = {
            "planner": {"model": "gpt-5", "unknown_field": "ignored"},  # Extra field
            "coder": {"model": "gpt-5"},
            "memory": {"vector_store_path": "/path"},
        }

        # Act
        result = validate_config(config_data)

        # Assert - Succeeds and ignores extra field
        assert result.is_ok()
        config = result.unwrap()
        assert config.planner.model == "gpt-5"
        # Extra field is silently ignored, not stored in model
        assert not hasattr(config.planner, "unknown_field")


class TestResultPatternCompliance:
    """Test Result pattern compliance (NECESSARY: Y - Yield tests)."""

    def test_successful_parse_returns_ok_result(self):
        """Test successful parsing returns Ok(AgencyConfig)."""
        # Arrange
        config_data = {
            "planner": {"model": "gpt-5"},
            "coder": {"model": "gpt-5"},
            "memory": {"vector_store_path": "/path"},
        }

        # Act
        result = validate_config(config_data)

        # Assert
        assert result.is_ok()
        assert not result.is_err()
        config = result.unwrap()
        assert isinstance(config, AgencyConfig)

    def test_failed_validation_returns_err_result(self):
        """Test failed validation returns Err(ConfigError)."""
        # Arrange
        config_data = {"planner": {}}  # Missing required fields

        # Act
        result = validate_config(config_data)

        # Assert
        assert result.is_err()
        assert not result.is_ok()
        error = result.unwrap_err()
        assert isinstance(error, ConfigError)

    def test_config_error_has_all_required_fields(self):
        """Test ConfigError structure has all required fields."""
        # Arrange
        config_data = {"planner": {"model": 123}}  # Type error

        # Act
        result = validate_config(config_data)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert hasattr(error, "error_type")
        assert hasattr(error, "field_path")
        assert hasattr(error, "message")
        assert hasattr(error, "suggestion")
        assert hasattr(error, "line_number")
        assert isinstance(error.error_type, ConfigErrorType)
        assert isinstance(error.field_path, str)
        assert isinstance(error.message, str)

    def test_config_error_str_formatting(self):
        """Test ConfigError __str__ formatting for display."""
        # Arrange
        config_data = {"planner": {}}  # Missing required field

        # Act
        result = validate_config(config_data)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        error_str = str(error)
        # Should contain error type and message
        assert error.error_type.value in error_str
        assert error.message in error_str
        # Should contain field path if present
        if error.field_path:
            assert error.field_path in error_str or "Field:" in error_str


class TestPydanticModels:
    """Test Pydantic model structure (NECESSARY: A - Accessibility)."""

    def test_agent_config_model_structure(self):
        """Test AgentConfig Pydantic model."""
        # Arrange & Act
        agent = AgentConfig(model="gpt-5", temperature=0.5, max_tokens=2000)

        # Assert
        assert agent.model == "gpt-5"
        assert agent.temperature == 0.5
        assert agent.max_tokens == 2000

    def test_memory_config_model_structure(self):
        """Test MemoryConfig Pydantic model."""
        # Arrange & Act
        memory = MemoryConfig(
            use_enhanced_memory=False, vector_store_path="/path", session_id="test_session"
        )

        # Assert
        assert memory.use_enhanced_memory is False
        assert memory.vector_store_path == "/path"
        assert memory.session_id == "test_session"

    def test_agency_config_model_structure(self):
        """Test AgencyConfig Pydantic model."""
        # Arrange
        planner = AgentConfig(model="gpt-5")
        coder = AgentConfig(model="gpt-5")
        memory = MemoryConfig(vector_store_path="/path")

        # Act
        config = AgencyConfig(planner=planner, coder=coder, memory=memory, log_level="DEBUG")

        # Assert
        assert config.planner == planner
        assert config.coder == coder
        assert config.memory == memory
        assert config.log_level == "DEBUG"

    def test_agent_config_defaults(self):
        """Test AgentConfig default values."""
        # Arrange & Act
        agent = AgentConfig(model="gpt-5")

        # Assert
        assert agent.temperature == 0.7  # Default
        assert agent.max_tokens == 4000  # Default

    def test_memory_config_defaults(self):
        """Test MemoryConfig default values."""
        # Arrange & Act
        memory = MemoryConfig(vector_store_path="/path")

        # Assert
        assert memory.use_enhanced_memory is True  # Default
        assert memory.session_id is None  # Default


class TestSpecificationCompliance:
    """Test specification acceptance criteria (NECESSARY: R - Regression)."""

    def test_ac_1_1_parse_valid_yaml_without_data_loss(self):
        """AC-1.1: Parse valid YAML files into Pydantic models without data loss."""
        # Arrange
        config_content = """
planner:
  model: custom-model-name
  temperature: 1.5
  max_tokens: 12345

coder:
  model: another-model
  temperature: 0.1
  max_tokens: 1

memory:
  use_enhanced_memory: false
  vector_store_path: /custom/path
  session_id: custom_session_123

log_level: ERROR
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert - No data loss
            assert result.is_ok()
            config = result.unwrap()
            assert config.planner.model == "custom-model-name"
            assert config.planner.temperature == 1.5
            assert config.planner.max_tokens == 12345
            assert config.coder.model == "another-model"
            assert config.coder.temperature == 0.1
            assert config.coder.max_tokens == 1
            assert config.memory.use_enhanced_memory is False
            assert config.memory.vector_store_path == "/custom/path"
            assert config.memory.session_id == "custom_session_123"
            assert config.log_level == "ERROR"
        finally:
            Path(temp_path).unlink()

    def test_ac_1_2_parse_valid_json_without_data_loss(self):
        """AC-1.2: Parse valid JSON files into Pydantic models without data loss."""
        # Arrange
        config_content = {
            "planner": {
                "model": "json-model",
                "temperature": 0.99,
                "max_tokens": 9999,
            },
            "coder": {"model": "coder-json-model", "temperature": 0.01, "max_tokens": 100},
            "memory": {
                "use_enhanced_memory": True,
                "vector_store_path": "/json/path",
                "session_id": "json_session",
            },
            "log_level": "WARNING",
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(config_content, f)
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert - No data loss
            assert result.is_ok()
            config = result.unwrap()
            assert config.planner.model == "json-model"
            assert config.planner.temperature == 0.99
            assert config.memory.session_id == "json_session"
            assert config.log_level == "WARNING"
        finally:
            Path(temp_path).unlink()

    def test_ac_3_1_all_parsing_functions_return_result(self):
        """AC-3.1: All parsing functions return Result[Config, ConfigError]."""
        # Arrange
        valid_config = {
            "planner": {"model": "gpt-5"},
            "coder": {"model": "gpt-5"},
            "memory": {"vector_store_path": "/path"},
        }

        # Act
        result = validate_config(valid_config)

        # Assert - Returns Result type
        assert hasattr(result, "is_ok")
        assert hasattr(result, "is_err")
        assert hasattr(result, "unwrap")
        assert hasattr(result, "unwrap_err")

    def test_ac_4_4_validate_positive_integer_constraint(self):
        """AC-4.4: Validate constraints (positive integers for max_tokens)."""
        # Arrange - Invalid (negative)
        config_negative = {
            "planner": {"model": "gpt-5", "max_tokens": -100},
            "coder": {"model": "gpt-5"},
            "memory": {"vector_store_path": "/path"},
        }

        # Act
        result = validate_config(config_negative)

        # Assert - Should fail constraint
        assert result.is_err()

    def test_ac_u_1_error_messages_include_field_path(self):
        """AC-U.1: Error messages include field path (e.g., agents.planner.model)."""
        # Arrange
        config_data = {
            "planner": {"model": 123},  # Type error
            "coder": {"model": "gpt-5"},
            "memory": {"vector_store_path": "/path"},
        }

        # Act
        result = validate_config(config_data)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert error.field_path  # Has field path
        assert "planner" in error.field_path or "model" in error.field_path


class TestIntegrationScenarios:
    """Test integration scenarios from spec examples."""

    def test_journey_2_typo_field_ignored_by_pydantic(self):
        """Test Journey 2: Typo in field name (Pydantic ignores extra fields by default)."""
        # Arrange - "modell" typo (Pydantic v2 ignores extra fields, doesn't error)
        config_content = """
planner:
  model: gpt-5
  modell: typo_value

coder:
  model: gpt-5

memory:
  vector_store_path: /path
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert - Succeeds (extra field silently ignored)
            # Note: To detect typos, would need Pydantic extra='forbid' config
            assert result.is_ok()
            config = result.unwrap()
            assert config.planner.model == "gpt-5"
        finally:
            Path(temp_path).unlink()

    def test_journey_3_missing_required_field_detection(self):
        """Test Journey 3: Missing required field detection."""
        # Arrange - Missing API key (simulated as missing vector_store_path)
        config_content = """
planner:
  model: gpt-5

coder:
  model: gpt-5

memory:
  use_enhanced_memory: true
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            # Act
            result = parse_config_file(temp_path)

            # Assert - Detects missing field
            assert result.is_err()
            error = result.unwrap_err()
            assert error.error_type == ConfigErrorType.MISSING_FIELD
            assert "vector_store_path" in error.field_path
            assert error.suggestion is not None
        finally:
            Path(temp_path).unlink()
