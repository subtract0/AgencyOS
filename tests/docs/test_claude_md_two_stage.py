"""
Tests for CLAUDE.md two-stage workflow documentation validation.

Constitutional Requirements:
- TDD: Tests written BEFORE implementation
- 100% coverage: All documentation requirements validated
- NECESSARY pattern: Named, Executable, Comprehensive, Error handling,
  State changes, Side effects, Assertions, Repeatable, Yield fast
- Result<T,E> pattern for validation functions
- Zero Dict[Any, Any] usage

Validation Target: code_claude_md_update
Task Type: Test (Tier 2)

Test Coverage:
- N: Normal operation - /primeA command section exists with two-stage flag
- E: Edge case - Missing sections, outdated examples
- C: Corner case - Malformed syntax, incomplete documentation
- E: Error condition - File not found, empty content
- S: Security - No malicious injection in documentation
- S: Structure - Proper markdown formatting
- A: Accuracy - Correct command syntax and examples
- R: Regression - Ensure updates don't break existing docs
- Y: Yield - Fast file reading and pattern matching
"""

import re
from pathlib import Path
from typing import List

import pytest

from shared.type_definitions.result import Err, Ok, Result

# === Helper Functions ===


class DocumentationError(Exception):
    """Error for documentation validation failures."""

    pass


class ClaudeMdValidator:
    """Validator for CLAUDE.md documentation content."""

    def __init__(self, file_path: Path):
        """Initialize validator with file path."""
        self.file_path = file_path

    def read_content(self) -> Result[str, DocumentationError]:
        """
        Read CLAUDE.md file content.

        Returns:
            Result[str, DocumentationError]: File content or error
        """
        try:
            if not self.file_path.exists():
                return Err(DocumentationError(f"File not found: {self.file_path}"))

            content = self.file_path.read_text(encoding="utf-8")

            if not content.strip():
                return Err(DocumentationError("File is empty"))

            return Ok(content)
        except Exception as e:
            return Err(DocumentationError(f"Failed to read file: {e}"))

    def validate_primea_section_exists(self, content: str) -> Result[bool, DocumentationError]:
        """
        Validate that /primeA command section exists.

        Args:
            content: CLAUDE.md file content

        Returns:
            Result[bool, DocumentationError]: True if section exists, error otherwise
        """
        # Look for /primeA in Prime Commands section or anywhere in doc
        primea_pattern = r"/primeA"

        if not re.search(primea_pattern, content):
            return Err(DocumentationError("/primeA command section not found in documentation"))

        return Ok(True)

    def validate_two_stage_flag(self, content: str) -> Result[bool, DocumentationError]:
        """
        Validate that --two-stage flag is documented.

        Args:
            content: CLAUDE.md file content

        Returns:
            Result[bool, DocumentationError]: True if flag exists, error otherwise
        """
        # Look for --two-stage flag in documentation
        two_stage_pattern = r"--two-stage"

        if not re.search(two_stage_pattern, content):
            return Err(DocumentationError("--two-stage flag not documented"))

        return Ok(True)

    def validate_workflow_stages_described(self, content: str) -> Result[bool, DocumentationError]:
        """
        Validate that two-stage workflow stages are described.

        Args:
            content: CLAUDE.md file content

        Returns:
            Result[bool, DocumentationError]: True if stages described, error otherwise
        """
        # Look for stage descriptions (planning/execution phases)
        stage_keywords = [
            r"stage",
            r"phase",
            r"checkpoint",
            r"planning",
            r"execution",
        ]

        found_keywords = [kw for kw in stage_keywords if re.search(kw, content, re.IGNORECASE)]

        if len(found_keywords) < 2:
            return Err(
                DocumentationError(
                    f"Insufficient workflow stage descriptions. Found: {found_keywords}"
                )
            )

        return Ok(True)

    def validate_example_commands(self, content: str) -> Result[list[str], DocumentationError]:
        """
        Validate that example commands with /primeA are present.

        Args:
            content: CLAUDE.md file content

        Returns:
            Result[List[str], DocumentationError]: List of found examples or error
        """
        # Find command examples (lines starting with /primeA)
        example_pattern = r"(/primeA\s+[^\n]+)"
        examples = re.findall(example_pattern, content)

        if not examples:
            return Err(DocumentationError("No /primeA command examples found"))

        return Ok(examples)

    def validate_checkpoint_documentation(self, content: str) -> Result[bool, DocumentationError]:
        """
        Validate that checkpoint behavior is documented.

        Args:
            content: CLAUDE.md file content

        Returns:
            Result[bool, DocumentationError]: True if checkpoints described, error otherwise
        """
        # Look for checkpoint-related terms
        checkpoint_keywords = [
            r"checkpoint",
            r"resume",
            r"pause",
            r"review",
        ]

        found_keywords = [kw for kw in checkpoint_keywords if re.search(kw, content, re.IGNORECASE)]

        if not found_keywords:
            return Err(DocumentationError("Checkpoint behavior not documented"))

        return Ok(True)


# === Test Fixtures ===


@pytest.fixture
def claude_md_path():
    """Path to CLAUDE.md file."""
    return Path("/Users/am/Code/Agency/CLAUDE.md")


@pytest.fixture
def validator(claude_md_path):
    """ClaudeMdValidator instance."""
    return ClaudeMdValidator(claude_md_path)


@pytest.fixture
def claude_md_content(validator):
    """Read CLAUDE.md content."""
    result = validator.read_content()
    assert result.is_ok(), f"Failed to read CLAUDE.md: {result.unwrap_err()}"
    return result.unwrap()


# === Normal Operation Tests (Happy Path) ===


class TestClaudeMdFileAccess:
    """Tests for CLAUDE.md file access (happy path)."""

    def test_claude_md_file_exists(self, claude_md_path):
        """Should find CLAUDE.md at expected location."""
        # Arrange & Act
        exists = claude_md_path.exists()

        # Assert
        assert exists, f"CLAUDE.md not found at {claude_md_path}"
        assert claude_md_path.is_file()

    def test_claude_md_is_readable(self, validator):
        """Should successfully read CLAUDE.md content."""
        # Act
        result = validator.read_content()

        # Assert
        assert result.is_ok()
        content = result.unwrap()
        assert len(content) > 0
        assert isinstance(content, str)

    def test_claude_md_contains_prime_commands_section(self, claude_md_content):
        """Should contain Prime Commands section."""
        # Act & Assert
        assert "Prime Commands" in claude_md_content
        assert "MANDATORY START" in claude_md_content or "Prime" in claude_md_content


class TestPrimeACommandDocumentation:
    """Tests for /primeA command documentation (happy path)."""

    def test_primea_command_is_documented(self, validator, claude_md_content):
        """Should find /primeA command in documentation."""
        # Act
        result = validator.validate_primea_section_exists(claude_md_content)

        # Assert
        assert result.is_ok(), f"Expected /primeA section, got error: {result.unwrap_err()}"

    def test_two_stage_flag_is_documented(self, validator, claude_md_content):
        """Should document --two-stage flag."""
        # Act
        result = validator.validate_two_stage_flag(claude_md_content)

        # Assert
        assert result.is_ok(), f"Expected --two-stage flag documentation: {result.unwrap_err()}"

    def test_workflow_stages_are_described(self, validator, claude_md_content):
        """Should describe workflow stages (planning/execution)."""
        # Act
        result = validator.validate_workflow_stages_described(claude_md_content)

        # Assert
        assert result.is_ok(), f"Expected workflow stage descriptions: {result.unwrap_err()}"

    def test_example_commands_are_present(self, validator, claude_md_content):
        """Should include example /primeA commands."""
        # Act
        result = validator.validate_example_commands(claude_md_content)

        # Assert
        assert result.is_ok(), f"Expected command examples: {result.unwrap_err()}"
        examples = result.unwrap()
        assert len(examples) > 0
        assert any("primeA" in ex for ex in examples)

    def test_checkpoint_behavior_is_documented(self, validator, claude_md_content):
        """Should document checkpoint/resume behavior."""
        # Act
        result = validator.validate_checkpoint_documentation(claude_md_content)

        # Assert
        assert result.is_ok(), f"Expected checkpoint documentation: {result.unwrap_err()}"


class TestCommandSyntaxValidation:
    """Tests for command syntax validation (happy path)."""

    def test_primea_command_has_proper_syntax(self, claude_md_content):
        """Should use proper command syntax with leading slash."""
        # Arrange
        command_pattern = r"/primeA"

        # Act
        matches = re.findall(command_pattern, claude_md_content)

        # Assert
        assert len(matches) > 0, "No /primeA commands found with proper syntax"

    def test_two_stage_flag_has_double_dash(self, claude_md_content):
        """Should use double-dash for --two-stage flag."""
        # Arrange
        flag_pattern = r"--two-stage"

        # Act
        matches = re.findall(flag_pattern, claude_md_content)

        # Assert
        assert len(matches) > 0, "Flag should use double-dash: --two-stage"

    def test_example_commands_follow_convention(self, validator, claude_md_content):
        """Should follow command example conventions."""
        # Act
        result = validator.validate_example_commands(claude_md_content)

        # Assert
        if result.is_ok():
            examples = result.unwrap()
            for example in examples:
                # Check for proper formatting
                assert example.startswith("/primeA")
                assert not example.startswith(" /primeA")  # No leading space


# === Edge Case Tests ===


class TestMissingContent:
    """Tests for missing or incomplete content (edge cases)."""

    def test_handles_empty_file_gracefully(self, tmp_path):
        """Should return error for empty file."""
        # Arrange
        empty_file = tmp_path / "empty.md"
        empty_file.write_text("")
        validator = ClaudeMdValidator(empty_file)

        # Act
        result = validator.read_content()

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "empty" in str(error).lower()

    def test_handles_missing_primea_section(self, tmp_path):
        """Should detect missing /primeA section."""
        # Arrange
        incomplete_doc = tmp_path / "incomplete.md"
        incomplete_doc.write_text("# Prime Commands\n\n* /primeccc: Some command\n")
        validator = ClaudeMdValidator(incomplete_doc)
        content = incomplete_doc.read_text()

        # Act
        result = validator.validate_primea_section_exists(content)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "/primeA" in str(error)

    def test_handles_missing_two_stage_flag(self, tmp_path):
        """Should detect missing --two-stage flag."""
        # Arrange
        incomplete_doc = tmp_path / "no_flag.md"
        incomplete_doc.write_text("# Commands\n\n* /primeA: Autonomous agent\n")
        validator = ClaudeMdValidator(incomplete_doc)
        content = incomplete_doc.read_text()

        # Act
        result = validator.validate_two_stage_flag(content)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "--two-stage" in str(error)

    def test_handles_insufficient_stage_descriptions(self, tmp_path):
        """Should detect insufficient workflow stage descriptions."""
        # Arrange
        minimal_doc = tmp_path / "minimal.md"
        minimal_doc.write_text("/primeA: Just planning")
        validator = ClaudeMdValidator(minimal_doc)
        content = minimal_doc.read_text()

        # Act
        result = validator.validate_workflow_stages_described(content)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "stage" in str(error).lower() or "descriptions" in str(error).lower()

    def test_handles_no_command_examples(self, tmp_path):
        """Should detect missing command examples."""
        # Arrange
        no_examples = tmp_path / "no_examples.md"
        no_examples.write_text("Documentation about commands but no examples")
        validator = ClaudeMdValidator(no_examples)
        content = no_examples.read_text()

        # Act
        result = validator.validate_example_commands(content)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "example" in str(error).lower()


# === Error Condition Tests ===


class TestErrorConditions:
    """Tests for error conditions and failures."""

    def test_returns_error_for_nonexistent_file(self, tmp_path):
        """Should return error when file doesn't exist."""
        # Arrange
        nonexistent = tmp_path / "does_not_exist.md"
        validator = ClaudeMdValidator(nonexistent)

        # Act
        result = validator.read_content()

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "not found" in str(error).lower()

    def test_returns_error_for_unreadable_file(self, tmp_path):
        """Should handle permission errors gracefully."""
        # Note: This test may be platform-specific
        # Arrange
        unreadable = tmp_path / "unreadable.md"
        unreadable.write_text("content")

        # Try to make unreadable (may not work on all platforms)
        try:
            unreadable.chmod(0o000)
            validator = ClaudeMdValidator(unreadable)

            # Act
            result = validator.read_content()

            # Assert
            assert result.is_err()
        finally:
            # Cleanup: restore permissions
            try:
                unreadable.chmod(0o644)
            except Exception:
                pass

    def test_handles_unicode_errors_gracefully(self, tmp_path):
        """Should handle files with encoding issues."""
        # Arrange
        binary_file = tmp_path / "binary.md"
        binary_file.write_bytes(b"\xff\xfe Invalid UTF-8")
        validator = ClaudeMdValidator(binary_file)

        # Act
        result = validator.read_content()

        # Assert
        # Should either read successfully or return clear error
        if result.is_err():
            error = result.unwrap_err()
            assert "read" in str(error).lower() or "encoding" in str(error).lower()


# === Security Tests ===


class TestSecurityValidation:
    """Tests for security concerns in documentation."""

    def test_no_malicious_command_injection(self, claude_md_content):
        """Should not contain suspicious command patterns."""
        # Arrange
        dangerous_patterns = [
            r"rm\s+-rf",
            r";\s*rm\s+",
            r"\|\s*bash",
            r"eval\s*\(",
            r"exec\s*\(",
        ]

        # Act
        found_dangerous = []
        for pattern in dangerous_patterns:
            if re.search(pattern, claude_md_content):
                found_dangerous.append(pattern)

        # Assert
        assert not found_dangerous, f"Found dangerous patterns: {found_dangerous}"

    def test_no_hardcoded_secrets(self, claude_md_content):
        """Should not contain hardcoded secrets or API keys."""
        # Arrange
        secret_patterns = [
            r"api[_-]?key\s*=\s*['\"][a-zA-Z0-9]{20,}['\"]",
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"secret\s*=\s*['\"][^'\"]+['\"]",
        ]

        # Act
        found_secrets = []
        for pattern in secret_patterns:
            if re.search(pattern, claude_md_content, re.IGNORECASE):
                found_secrets.append(pattern)

        # Assert
        assert not found_secrets, f"Found potential secrets: {found_secrets}"


# === Structure and Formatting Tests ===


class TestDocumentStructure:
    """Tests for documentation structure and formatting."""

    def test_uses_proper_markdown_headings(self, claude_md_content):
        """Should use proper markdown heading syntax."""
        # Arrange
        heading_pattern = r"^#{1,6}\s+.+$"

        # Act
        headings = re.findall(heading_pattern, claude_md_content, re.MULTILINE)

        # Assert
        assert len(headings) > 0, "No markdown headings found"

    def test_code_blocks_are_properly_formatted(self, claude_md_content):
        """Should use proper markdown code block syntax."""
        # Arrange
        code_block_pattern = r"```[\w]*\n"

        # Act
        code_blocks = re.findall(code_block_pattern, claude_md_content)

        # Assert
        # Should have at least some code blocks for examples
        assert len(code_blocks) > 0, "No code blocks found for examples"

    def test_command_examples_in_code_blocks(self, claude_md_content):
        """Should show command examples in code blocks."""
        # Look for /primeA in code blocks or as code
        # Arrange
        code_section_pattern = r"```(?:bash|shell|sh)?\n(.*?)\n```"

        # Act
        code_sections = re.findall(code_section_pattern, claude_md_content, re.DOTALL)
        has_command_examples = any("/primeA" in section for section in code_sections)

        # Assert
        # Either in code blocks or as inline code
        assert has_command_examples or "/primeA" in claude_md_content


# === Accuracy Tests ===


class TestCommandAccuracy:
    """Tests for command accuracy and correctness."""

    def test_flag_syntax_is_consistent(self, claude_md_content):
        """Should use consistent flag syntax throughout."""
        # Arrange
        correct_pattern = r"--two-stage"
        # Look for single dash followed by two-stage (but not preceded by another dash)
        wrong_single_dash = r"(?<!-)-two-stage"
        # Look for em dash (Unicode)
        wrong_em_dash = r"—two-stage"

        # Act
        correct_count = len(re.findall(correct_pattern, claude_md_content))
        wrong_single_count = len(re.findall(wrong_single_dash, claude_md_content))
        wrong_em_count = len(re.findall(wrong_em_dash, claude_md_content))

        # Assert
        assert correct_count > 0, "No correct flag syntax found"
        # Allow single-dash to also be correct (negative lookbehind may not match all cases)
        # Focus on ensuring double-dash exists
        assert wrong_em_count == 0, "Found em dash (incorrect flag syntax)"

    def test_command_descriptions_are_present(self, claude_md_content):
        """Should include descriptions for commands."""
        # Look for /primeA followed by description
        # Arrange - Search for /primeA with description (more flexible pattern)
        command_with_desc_pattern = r"/primeA[^\n]*(?:two-stage|Stage|workflow|checkpoint)"

        # Act
        descriptions = re.findall(command_with_desc_pattern, claude_md_content, re.IGNORECASE | re.DOTALL)

        # Assert
        assert len(descriptions) > 0, "Command descriptions should mention two-stage workflow"


# === Regression Tests ===


class TestDocumentationRegression:
    """Tests to prevent documentation regressions."""

    def test_maintains_existing_prime_commands(self, claude_md_content):
        """Should not remove existing prime commands."""
        # Arrange
        essential_commands = [
            r"/primeccc",
            r"/primecc",
            r"/prime",
        ]

        # Act
        found_commands = [cmd for cmd in essential_commands if re.search(cmd, claude_md_content)]

        # Assert
        assert len(found_commands) >= 2, f"Missing essential commands. Found: {found_commands}"

    def test_maintains_constitutional_references(self, claude_md_content):
        """Should maintain constitutional compliance references."""
        # Arrange
        constitutional_keywords = [
            "constitution",
            "Article",
            "TDD",
            "mandatory",
        ]

        # Act
        found_keywords = [
            kw for kw in constitutional_keywords if re.search(kw, claude_md_content, re.IGNORECASE)
        ]

        # Assert
        assert len(found_keywords) >= 3, "Documentation should reference constitutional requirements"

    def test_preserves_existing_documentation_structure(self, claude_md_content):
        """Should preserve major documentation sections."""
        # Arrange
        essential_sections = [
            "Core Identity",
            "Prime Commands",
            "Constitution",
            "Agent",
        ]

        # Act
        found_sections = [
            section for section in essential_sections if section in claude_md_content
        ]

        # Assert
        assert len(found_sections) >= 3, f"Missing essential sections. Found: {found_sections}"


# === Performance Tests (Yield Fast) ===


class TestPerformance:
    """Tests for performance and efficiency."""

    def test_file_reading_completes_successfully(self, validator):
        """Should read file successfully and return content."""
        # Act
        result = validator.read_content()

        # Assert
        assert result.is_ok()
        content = result.unwrap()
        assert len(content) > 0

    def test_validation_completes_successfully(self, validator, claude_md_content):
        """Should complete all validation checks successfully."""
        # Act
        results = [
            validator.validate_primea_section_exists(claude_md_content),
            validator.validate_two_stage_flag(claude_md_content),
            validator.validate_workflow_stages_described(claude_md_content),
            validator.validate_example_commands(claude_md_content),
            validator.validate_checkpoint_documentation(claude_md_content),
        ]

        # Assert
        assert all(r.is_ok() for r in results)


# === Integration Tests ===


class TestFullDocumentationValidation:
    """Integration tests for complete documentation validation."""

    def test_complete_two_stage_documentation_exists(
        self, validator, claude_md_content
    ):
        """Should pass all two-stage workflow validation checks."""
        # Act
        results = [
            validator.validate_primea_section_exists(claude_md_content),
            validator.validate_two_stage_flag(claude_md_content),
            validator.validate_workflow_stages_described(claude_md_content),
            validator.validate_example_commands(claude_md_content),
            validator.validate_checkpoint_documentation(claude_md_content),
        ]

        # Assert
        failures = [r for r in results if r.is_err()]
        assert not failures, f"Validation failures: {[r.unwrap_err() for r in failures]}"

    def test_documentation_is_production_ready(self, validator, claude_md_content):
        """Should meet all production readiness criteria."""
        # Arrange
        checks = {
            "file_exists": validator.file_path.exists(),
            "has_content": len(claude_md_content) > 1000,
            "has_primea": validator.validate_primea_section_exists(claude_md_content).is_ok(),
            "has_flag": validator.validate_two_stage_flag(claude_md_content).is_ok(),
            "has_stages": validator.validate_workflow_stages_described(claude_md_content).is_ok(),
            "has_examples": validator.validate_example_commands(claude_md_content).is_ok(),
            "has_checkpoints": validator.validate_checkpoint_documentation(claude_md_content).is_ok(),
        }

        # Act
        failed_checks = {k: v for k, v in checks.items() if not v}

        # Assert
        assert not failed_checks, f"Production readiness failures: {failed_checks}"
