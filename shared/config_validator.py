"""Configuration File Validator for Agency OS.

Validates YAML/JSON configuration files with strict typing and Result pattern.

Constitutional Compliance:
- Article I: Complete context (read entire file before validation)
- Article II: 100% verification (tests will verify in next task)
- Article IV: Apply learnings (Pydantic models, Result pattern)
- Article V: Trace to spec (implements spec-primeA-demo-config-validator.md)
- Law #2: Strict typing (no Dict[Any, Any])
- Law #5: Result pattern for error handling
- Law #8: Functions <50 lines
"""

import json
from enum import Enum
from pathlib import Path
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, Field, ValidationError

from shared.type_definitions.result import Err, Ok, Result


class ConfigErrorType(str, Enum):
    """Configuration error categories."""

    SYNTAX_ERROR = "syntax_error"
    VALIDATION_ERROR = "validation_error"
    MISSING_FIELD = "missing_field"
    TYPE_MISMATCH = "type_mismatch"
    UNKNOWN_FIELD = "unknown_field"
    FILE_NOT_FOUND = "file_not_found"
    UNSUPPORTED_FORMAT = "unsupported_format"


class ConfigError(BaseModel):
    """Structured configuration error with actionable messages."""

    error_type: ConfigErrorType = Field(..., description="Error category")
    field_path: str = Field(..., description="Dotted path to field (e.g., 'agents.planner.model')")
    message: str = Field(..., description="Human-readable error message")
    suggestion: str | None = Field(default=None, description="Suggested fix for common mistakes")
    line_number: int | None = Field(default=None, description="Line number in file (YAML only)")

    def __str__(self) -> str:
        """Format error for display."""
        parts = [f"{self.error_type.value}: {self.message}"]
        if self.field_path:
            parts.append(f"  Field: {self.field_path}")
        if self.line_number:
            parts.append(f"  Line: {self.line_number}")
        if self.suggestion:
            parts.append(f"  Suggestion: {self.suggestion}")
        return "\n".join(parts)


class AgentConfig(BaseModel):
    """Configuration for individual agent."""

    model: str = Field(..., description="LLM model name (e.g., 'gpt-5', 'gpt-4o')")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=4000, gt=0, description="Maximum tokens per request")


class MemoryConfig(BaseModel):
    """Configuration for memory system."""

    use_enhanced_memory: bool = Field(
        default=True, description="Enable VectorStore integration (Article IV)"
    )
    vector_store_path: str = Field(..., description="Path to VectorStore data")
    session_id: str | None = Field(None, description="Optional session identifier")


class AgencyConfig(BaseModel):
    """Root configuration for Agency system."""

    planner: AgentConfig = Field(..., description="Planner agent configuration")
    coder: AgentConfig = Field(..., description="Coder agent configuration")
    memory: MemoryConfig = Field(..., description="Memory system configuration")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )


def _detect_file_format(file_path: Path) -> Result[Literal["yaml", "json"], ConfigError]:
    """Detect file format from extension.

    Args:
        file_path: Path to configuration file

    Returns:
        Result with format ('yaml' or 'json') or ConfigError

    Constitutional: Law #8 (focused function <50 lines)
    """
    suffix = file_path.suffix.lower()

    if suffix in {".yaml", ".yml"}:
        return Ok("yaml")
    if suffix == ".json":
        return Ok("json")

    return Err(
        ConfigError(
            error_type=ConfigErrorType.UNSUPPORTED_FORMAT,
            field_path="",
            message=f"Unsupported file format: {suffix}",
            suggestion="Use .yaml, .yml, or .json extension",
        )
    )


def _parse_yaml(content: str, file_path: str) -> Result[dict[str, Any], ConfigError]:
    """Parse YAML content into dictionary.

    Args:
        content: Raw YAML string
        file_path: File path for error reporting

    Returns:
        Result with parsed dict or ConfigError

    Constitutional: Law #5 (Result pattern), Law #8 (<50 lines)
    """
    try:
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            return Err(
                ConfigError(
                    error_type=ConfigErrorType.SYNTAX_ERROR,
                    field_path="",
                    message=f"YAML root must be an object, got {type(data).__name__}",
                    suggestion="Ensure YAML file starts with key-value pairs",
                )
            )
        return Ok(data)
    except yaml.YAMLError as e:
        line_number = getattr(e, "problem_mark", None)
        line_num = line_number.line + 1 if line_number else None

        return Err(
            ConfigError(
                error_type=ConfigErrorType.SYNTAX_ERROR,
                field_path="",
                message=f"YAML parsing failed: {str(e)}",
                line_number=line_num,
            )
        )


def _parse_json(content: str, file_path: str) -> Result[dict[str, Any], ConfigError]:
    """Parse JSON content into dictionary.

    Args:
        content: Raw JSON string
        file_path: File path for error reporting

    Returns:
        Result with parsed dict or ConfigError

    Constitutional: Law #5 (Result pattern), Law #8 (<50 lines)
    """
    try:
        data = json.loads(content)
        if not isinstance(data, dict):
            return Err(
                ConfigError(
                    error_type=ConfigErrorType.SYNTAX_ERROR,
                    field_path="",
                    message=f"JSON root must be an object, got {type(data).__name__}",
                    suggestion="Ensure JSON file starts with {{ ... }}",
                )
            )
        return Ok(data)
    except json.JSONDecodeError as e:
        return Err(
            ConfigError(
                error_type=ConfigErrorType.SYNTAX_ERROR,
                field_path="",
                message=f"JSON parsing failed at position {e.pos}: {e.msg}",
                line_number=e.lineno,
                suggestion="Check for missing commas, quotes, or brackets",
            )
        )


def validate_config(data: dict[str, Any]) -> Result[AgencyConfig, ConfigError]:
    """Validate configuration data against schema.

    Args:
        data: Parsed configuration dictionary

    Returns:
        Result with validated AgencyConfig or ConfigError

    Constitutional:
    - Law #2: Strict typing (no Dict[Any, Any])
    - Law #5: Result pattern for validation errors
    - Law #8: Focused function <50 lines
    """
    try:
        config = AgencyConfig(**data)
        return Ok(config)
    except ValidationError as e:
        # Extract first error for clarity
        first_error = e.errors()[0]
        field_path = ".".join(str(loc) for loc in first_error["loc"])
        error_msg = first_error["msg"]
        error_type_str = first_error["type"]

        # Determine error category
        if "missing" in error_type_str:
            error_type = ConfigErrorType.MISSING_FIELD
            suggestion = f"Add required field '{field_path}' to configuration"
        elif "extra" in error_type_str or "unexpected" in error_type_str.lower():
            error_type = ConfigErrorType.UNKNOWN_FIELD
            # Simple typo detection (could be enhanced with fuzzy matching)
            field_name = field_path.split(".")[-1]
            suggestion = f"Unknown field '{field_name}'. Check spelling or remove if not needed"
        else:
            error_type = ConfigErrorType.VALIDATION_ERROR
            suggestion = None

        return Err(
            ConfigError(
                error_type=error_type,
                field_path=field_path,
                message=error_msg,
                suggestion=suggestion,
            )
        )


def _read_config_file(file_path: Path) -> Result[str, ConfigError]:
    """Read configuration file content.

    Args:
        file_path: Path to configuration file

    Returns:
        Result with file content or ConfigError

    Constitutional: Law #8 (<50 lines)
    """
    if not file_path.exists():
        return Err(
            ConfigError(
                error_type=ConfigErrorType.FILE_NOT_FOUND,
                field_path="",
                message=f"Configuration file not found: {file_path}",
                suggestion="Check file path and ensure file exists",
            )
        )

    try:
        return Ok(file_path.read_text(encoding="utf-8"))
    except Exception as e:
        return Err(
            ConfigError(
                error_type=ConfigErrorType.SYNTAX_ERROR,
                field_path="",
                message=f"Failed to read file: {str(e)}",
                suggestion="Ensure file is readable and UTF-8 encoded",
            )
        )


def parse_config_file(file_path: str) -> Result[AgencyConfig, ConfigError]:
    """Parse and validate configuration file.

    Args:
        file_path: Path to YAML or JSON configuration file

    Returns:
        Result with AgencyConfig on success or ConfigError on failure

    Constitutional:
    - Article I: Complete context (read entire file before validation)
    - Law #5: Result pattern (never raises exceptions for control flow)
    - Law #8: Orchestration function <50 lines
    """
    path = Path(file_path)

    # Detect format
    format_result = _detect_file_format(path)
    if format_result.is_err():
        return Err(format_result.unwrap_err())

    # Read file content (Article I: complete context)
    content_result = _read_config_file(path)
    if content_result.is_err():
        return Err(content_result.unwrap_err())

    # Parse based on format
    file_format = format_result.unwrap()
    content = content_result.unwrap()

    parse_result = (
        _parse_yaml(content, file_path)
        if file_format == "yaml"
        else _parse_json(content, file_path)
    )

    # Validate against Pydantic schema
    return parse_result.and_then(validate_config)
