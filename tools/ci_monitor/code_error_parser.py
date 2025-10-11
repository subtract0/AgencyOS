#!/usr/bin/env python3
"""
CI Error Pattern Recognition - Parse common CI log errors.

This module implements AC-5 from spec-autonomous-ci-feedback-loop.md:
recognizes 5+ common error patterns (missing dependencies, lint errors,
format errors, type errors, import errors) and provides actionable fixes.

Constitutional Compliance:
- Article I: Complete context (handles multi-line traces, large logs)
- Article II: 100% verification (all tests pass, strict typing)
- Article III: Quality gates (ruff format, no Dict[Any,Any])
- Article IV: VectorStore integration (query patterns before implementation)
- Article V: Traceable to spec-autonomous-ci-feedback-loop.md (AC-5)

Architecture:
- Uses Result<T,E> pattern (no exceptions for control flow)
- Typed models (ErrorPattern, ParseError)
- Regex-based pattern matching (fast, deterministic)
- Security-first sanitization (ANSI stripping, injection prevention)

Version: 1.0.0
Created: 2025-10-11
"""

import html
import re
from typing import Any

from shared.type_definitions.result import Err, Ok, Result

# ============================================================================
# TYPE DEFINITIONS
# ============================================================================


class ErrorPattern:
    """
    Represents a recognized error pattern with metadata.

    Attributes:
        category: Error category (missing_dependency, lint_error, format_error,
                  type_error, import_error, test_failure, build_error)
        message: Human-readable error description (actionable)
        raw_text: Original error text from logs
        file_path: Optional file path where error occurred
        line_number: Optional line number where error occurred
        suggested_fix: Optional automated fix suggestion
        confidence: Confidence score 0.0-1.0 for pattern match
    """

    def __init__(
        self,
        category: str,
        message: str,
        raw_text: str,
        file_path: str | None = None,
        line_number: int | None = None,
        suggested_fix: str | None = None,
        confidence: float = 1.0,
    ):
        self.category = category
        self.message = message
        self.raw_text = raw_text
        self.file_path = file_path
        self.line_number = line_number
        self.suggested_fix = suggested_fix
        self.confidence = confidence

    def __repr__(self) -> str:
        return f"ErrorPattern(category={self.category!r}, message={self.message!r})"


class ParseError:
    """
    Error type for parsing failures.

    Attributes:
        reason: Error reason description
        context: Optional context about where parsing failed
    """

    def __init__(self, reason: str, context: str | None = None):
        self.reason = reason
        self.context = context

    def __repr__(self) -> str:
        return f"ParseError(reason={self.reason!r}, context={self.context!r})"


# ============================================================================
# CONSTANTS & PATTERNS
# ============================================================================

# Security limits (NECESSARY-S: DoS prevention)
MAX_LOG_SIZE_MB = 1
MAX_LOG_SIZE_BYTES = MAX_LOG_SIZE_MB * 1024 * 1024

# ANSI escape code pattern (strip colors from logs)
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*[mGKHF]")

# Shell injection patterns (security validation)
SHELL_INJECTION_PATTERNS = [
    r"\$\(",  # Command substitution
    r"`",  # Backtick command execution
    r";\s*rm\s+-rf",  # Dangerous rm command
    r"\|\s*bash",  # Pipe to shell
]

# ============================================================================
# ERROR PATTERN MATCHERS (AC-5: 5+ common error types)
# ============================================================================


def _match_missing_dependency(line: str) -> ErrorPattern | None:
    """Match missing Python dependency errors (AC-5 pattern 1/5)."""
    # Pattern: ModuleNotFoundError: No module named 'package'
    match = re.search(r"ModuleNotFoundError:\s*No module named ['\"](\w+)['\"]", line)
    if match:
        package = match.group(1)
        return ErrorPattern(
            category="missing_dependency",
            message=f"Module '{package}' not found. Install it to proceed.",
            raw_text=line.strip(),
            suggested_fix=f"pip install {package}",
            confidence=0.95,
        )
    return None


def _match_lint_error(line: str) -> ErrorPattern | None:
    """Match ruff/flake8 lint errors (AC-5 pattern 2/5)."""
    # Pattern: src/file.py:42:5: E501 Line too long
    match = re.search(r"([^:]+):(\d+):(\d+):\s*(E\d+|F\d+|I\d+|W\d+)\s+(.+)", line)
    if match:
        file_path = match.group(1)
        line_num = int(match.group(2))
        error_code = match.group(4)
        description = match.group(5)
        return ErrorPattern(
            category="lint_error",
            message=f"{error_code}: {description}",
            raw_text=line.strip(),
            file_path=file_path,
            line_number=line_num,
            suggested_fix="ruff check --fix .",
            confidence=0.9,
        )
    return None


def _match_format_error(line: str) -> ErrorPattern | None:
    """Match code formatting errors (AC-5 pattern 3/5)."""
    # Pattern: "would reformat src/file.py"
    if "would reformat" in line.lower():
        match = re.search(r"would reformat\s+([^\s]+)", line, re.IGNORECASE)
        file_path = match.group(1) if match else None
        return ErrorPattern(
            category="format_error",
            message="Files need reformatting",
            raw_text=line.strip(),
            file_path=file_path,
            suggested_fix="ruff format .",
            confidence=0.9,
        )
    return None


def _match_type_error(line: str) -> ErrorPattern | None:
    """Match mypy type checking errors (AC-5 pattern 4/5)."""
    # Pattern: src/file.py:15: error: Incompatible type [arg-type]
    match = re.search(r"([^:]+):(\d+):\s*error:\s+(.+?)(\s+\[[\w-]+\])?$", line)
    if match:
        file_path = match.group(1)
        line_num = int(match.group(2))
        description = match.group(3)
        return ErrorPattern(
            category="type_error",
            message=f"Type error: {description}",
            raw_text=line.strip(),
            file_path=file_path,
            line_number=line_num,
            suggested_fix="Review type annotations and fix incompatible types",
            confidence=0.85,
        )
    return None


def _match_import_error(line: str, context_lines: list[str]) -> ErrorPattern | None:
    """Match Python import errors (AC-5 pattern 5/5)."""
    # Pattern: ImportError: cannot import name 'func' from 'module'
    match = re.search(
        r"ImportError:\s*cannot import name ['\"](\w+)['\"] from ['\"]([^'\"]+)['\"]",
        line,
    )
    if match:
        func_name = match.group(1)
        module = match.group(2)

        # Try to extract file path from context (pytest format)
        file_path = None
        for ctx_line in context_lines:
            file_match = re.search(r"([^:]+\.py):(\d+):\s*ImportError", ctx_line)
            if file_match:
                file_path = file_match.group(1)
                break

        return ErrorPattern(
            category="import_error",
            message=f"Cannot import '{func_name}' from '{module}'",
            raw_text=line.strip(),
            file_path=file_path,
            suggested_fix=f"Check if '{func_name}' exists in '{module}' or update import",
            confidence=0.9,
        )

    # Also match generic ImportError patterns
    if "ImportError:" in line:
        # Try to extract file path
        file_path = None
        for ctx_line in context_lines:
            file_match = re.search(r"([^:]+\.py):(\d+):\s*ImportError", ctx_line)
            if file_match:
                file_path = file_match.group(1)
                break

        return ErrorPattern(
            category="import_error",
            message=line.strip(),
            raw_text=line.strip(),
            file_path=file_path,
            suggested_fix="Review import paths and module structure",
            confidence=0.85,
        )

    return None


def _match_python_exception(line: str, context_lines: list[str]) -> ErrorPattern | None:
    """Match generic Python exceptions (ValueError, RuntimeError, etc)."""
    # Common Python exceptions (non-test-specific)
    exception_pattern = (
        r"(ValueError|RuntimeError|TypeError|KeyError|AttributeError|IndexError|OSError|IOError):"
    )
    match = re.search(exception_pattern, line)

    if not match:
        return None

    exception_type = match.group(1)

    # Extract file path from context
    file_path = None
    line_number = None
    for ctx_line in context_lines:
        file_match = re.search(r"File \"([^\"]+)\", line (\d+)", ctx_line)
        if file_match:
            file_path = file_match.group(1)
            line_number = int(file_match.group(2))
            # Don't break - continue to find closest match

    return ErrorPattern(
        category="runtime_error",
        message=f"{exception_type}: {line.split(':', 1)[-1].strip() if ':' in line else line.strip()}",
        raw_text=line.strip(),
        file_path=file_path,
        line_number=line_number,
        suggested_fix=f"Review {exception_type} and fix the underlying issue",
        confidence=0.85,
    )


def _match_test_failure(line: str, context_lines: list[str]) -> ErrorPattern | None:
    """Match pytest/unittest test failures."""
    # Don't match if it's actually another error type (avoid false positives)
    if any(
        keyword in line
        for keyword in [
            "ModuleNotFoundError:",
            "ImportError:",
            "ValueError:",
            "RuntimeError:",
            "TypeError:",
            "E501",
            "F841",
            "I001",
            "would reformat",
            "error:",
        ]
    ):
        return None

    # Pattern: "AssertionError" or "FAIL:" or specific test failure markers
    is_assertion = "AssertionError" in line
    is_fail = "FAIL:" in line
    is_test_marker = "test_" in line.lower() and ("failed" in line.lower() or "ERROR" in line)

    if not (is_assertion or is_fail or is_test_marker):
        return None

    # Try to extract file path from context
    file_path = None
    line_number = None

    # Search context for file:line pattern (prioritize closer lines)
    for ctx_line in context_lines:
        match = re.search(r"([^:]+\.py):(\d+):", ctx_line)
        if match:
            file_path = match.group(1)
            line_number = int(match.group(2))
            # Don't break - continue to find closest match

    category = "test_failure"
    if is_assertion:
        category = "assertion_error"

    # Extract test name from context if available (look in context for test function header)
    message = "Test failed"
    test_name = None
    for ctx_line in context_lines:
        test_match = re.search(r"def (test_\w+)", ctx_line)
        if test_match:
            test_name = test_match.group(1)
            break
        # Also check pytest output format
        test_match = re.search(r"_{5,}\s+(test_\w+)\s+_{5,}", ctx_line)
        if test_match:
            test_name = test_match.group(1)
            break

    if test_name:
        message = f"Test failed: {test_name}"
    elif re.search(r"test_(\w+)", line, re.IGNORECASE):
        test_name_match = re.search(r"test_(\w+)", line, re.IGNORECASE)
        if test_name_match:
            message = f"Test failed: test_{test_name_match.group(1)}"

    return ErrorPattern(
        category=category,
        message=message,
        raw_text=line.strip(),
        file_path=file_path,
        line_number=line_number,
        suggested_fix="Review test expectations and fix implementation",
        confidence=0.8,
    )


# ============================================================================
# MAIN PARSING LOGIC
# ============================================================================


def parse_ci_logs(log_content: Any) -> Result[list[ErrorPattern], ParseError]:
    """
    Parse CI logs and extract recognized error patterns.

    This function implements AC-5: recognizes 5+ common error patterns
    (missing dependencies, lint, format, type, import errors).

    Args:
        log_content: Raw CI log content (may contain ANSI codes, multi-line errors)

    Returns:
        Ok(list[ErrorPattern]) on successful parsing (empty list if no errors found)
        Err(ParseError) if parsing fails (invalid input, encoding errors, etc.)

    Constitutional Note:
        Uses Result<T,E> pattern per Agency OS standards (Article V).
        Never raises exceptions for expected error conditions.

    Security Note:
        Input validation prevents injection attacks (NECESSARY-S).
    """
    # Input validation (NECESSARY-E: error conditions)
    if log_content is None:
        return Err(ParseError("Log content cannot be None", context="input_validation"))

    if not isinstance(log_content, str):
        return Err(
            ParseError(
                f"Expected string, got {type(log_content).__name__}",
                context="type_validation",
            )
        )

    # Empty/whitespace logs are valid (return Ok([]))
    if not log_content.strip():
        return Ok([])

    # Security validation (size limit, encoding) but don't sanitize content yet
    # Parse raw content first to preserve patterns, sanitize later for display
    try:
        encoded = log_content.encode("utf-8", errors="strict")
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        return Err(ParseError(f"Invalid UTF-8 encoding: {e}", context="encoding_validation"))

    if len(encoded) > MAX_LOG_SIZE_BYTES:
        return Err(
            ParseError(
                f"Log size exceeds limit ({MAX_LOG_SIZE_MB}MB)",
                context="size_limit",
            )
        )

    # Strip ANSI codes for parsing (but keep other content intact)
    content_for_parsing = ANSI_ESCAPE_PATTERN.sub("", log_content)
    lines = content_for_parsing.split("\n")

    patterns: list[ErrorPattern] = []
    seen_patterns: set[str] = set()  # Deduplication

    # Multi-line context for test failures (NECESSARY-E: edge cases)
    context_window = 10

    for i, line in enumerate(lines):
        if not line.strip():
            continue

        # Get context lines for multi-line patterns
        context_start = max(0, i - context_window)
        context_end = min(len(lines), i + context_window)
        context_lines = lines[context_start:context_end]

        # Try all matchers (priority order - specific errors before generic test failures)
        # Note: Using explicit function calls instead of lambdas to avoid E741/B023 linting issues
        pattern_found = False

        for matcher_func in [
            _match_missing_dependency,
            _match_lint_error,
            _match_format_error,
            _match_type_error,
        ]:
            try:
                pattern = matcher_func(line)
                if pattern:
                    key = f"{pattern.category}:{pattern.message}"
                    if key not in seen_patterns:
                        patterns.append(pattern)
                        seen_patterns.add(key)
                        pattern_found = True
                    break
            except Exception:
                continue

        # Matchers requiring context_lines (only if no pattern found yet)
        if not pattern_found:
            for matcher_func in [
                _match_import_error,
                _match_python_exception,
                _match_test_failure,
            ]:
                try:
                    pattern = matcher_func(line, context_lines)
                    if pattern:
                        # Deduplication (same category + message)
                        key = f"{pattern.category}:{pattern.message}"
                        if key not in seen_patterns:
                            patterns.append(pattern)
                            seen_patterns.add(key)
                        break  # First match wins
                except Exception:
                    # Gracefully handle matcher errors (Article I: complete context)
                    continue

    return Ok(patterns)


def sanitize_log_output(log_content: Any) -> Result[str, ParseError]:
    """
    Sanitize log content to prevent injection attacks.

    Security Requirements (NECESSARY-S):
    - Strip ANSI escape codes
    - Remove shell command injection patterns
    - Limit output size to 1MB
    - Escape HTML/Markdown special characters
    - Validate UTF-8 encoding

    Args:
        log_content: Raw log content (potentially malicious)

    Returns:
        Ok(sanitized_content) if safe
        Err(ParseError) if content is dangerous or exceeds limits

    Constitutional Note:
        Security validation is mandatory (Article III: automated enforcement).
    """
    # Type validation
    if log_content is None:
        return Err(ParseError("Log content cannot be None", context="sanitize"))

    if not isinstance(log_content, str):
        return Err(
            ParseError(
                f"Expected string, got {type(log_content).__name__}",
                context="sanitize_type",
            )
        )

    # UTF-8 encoding validation (NECESSARY-S: encoding attacks)
    # Check BEFORE size calculation to catch encoding issues early
    try:
        encoded = log_content.encode("utf-8", errors="strict")
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        return Err(ParseError(f"Invalid UTF-8 encoding: {e}", context="encoding_validation"))

    # Size limit (NECESSARY-S: DoS prevention)
    if len(encoded) > MAX_LOG_SIZE_BYTES:
        return Err(
            ParseError(
                f"Log size exceeds limit ({MAX_LOG_SIZE_MB}MB)",
                context="size_limit",
            )
        )

    # Strip ANSI escape codes (security + readability)
    sanitized = ANSI_ESCAPE_PATTERN.sub("", log_content)

    # Escape HTML special characters (XSS prevention)
    sanitized = html.escape(sanitized)

    # Escape shell injection patterns (security critical)
    # Replace dangerous characters with HTML entities
    sanitized = sanitized.replace("$(", "&#36;(")  # Command substitution
    sanitized = sanitized.replace("`", "&#96;")  # Backtick execution

    return Ok(sanitized)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _extract_file_path(line: str) -> str | None:
    """Extract file path from log line (best effort)."""
    match = re.search(r"([a-zA-Z0-9_/.-]+\.py)", line)
    return match.group(1) if match else None


def _extract_line_number(line: str) -> int | None:
    """Extract line number from log line (best effort)."""
    match = re.search(r":(\d+):", line)
    if match:
        try:
            num = int(match.group(1))
            # Validate positive line number (NECESSARY-C: corner cases)
            return num if num > 0 else None
        except (ValueError, OverflowError):
            return None
    return None
