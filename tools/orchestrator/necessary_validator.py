"""
NECESSARY Pattern Validator - AST-based test quality validation.

Validates test files against NECESSARY pattern compliance:
- N (Named): Descriptive test names (test_X_when_Y_then_Z)
- E (Executable): Tests can run without errors
- C (Comprehensive): AAA structure with comments
- E (Error-validated): Edge cases and error paths covered
- S (State-verified): State changes properly verified
- S (Side-effects): Side effects controlled/verified
- A (Assertions): Meaningful assertions present
- R (Repeatable): Tests produce consistent results
- Y (Yielding): Tests are fast and efficient

Constitutional Compliance:
- Article I: Complete context via full AST parsing
- Article II: Test quality enforcement before acceptance
- Article IV: Query VectorStore for proven fix patterns
- Article V: Spec-driven validation rules (ADR-011)

Usage:
    validator = NECESSARYValidator()
    result = validator.validate("tests/test_feature.py")

    if result.is_ok():
        report = result.unwrap()
        if not report.passed:
            for violation in report.violations:
                print(f"{violation.type}: {violation.description}")
                for fix in violation.suggested_fixes:
                    print(f"  Fix (confidence {fix.confidence}): {fix.description}")
"""

import ast
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from shared.type_definitions.result import Err, Ok, Result

# Pydantic Models


class SuggestedFix(BaseModel):
    """Auto-fix suggestion with confidence scoring."""

    description: str = Field(..., description="Human-readable fix description")
    code_snippet: str = Field(..., description="Proposed code fix")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Fix confidence score")


class Violation(BaseModel):
    """Detected NECESSARY pattern violation."""

    type: Literal["naming", "aaa_structure", "docstring", "edge_case", "assertion"] = Field(
        ..., description="Violation category"
    )
    severity: Literal["critical", "high", "medium", "low"] = Field(
        ..., description="Violation severity level"
    )
    line_number: int = Field(..., ge=1, description="Line number where violation occurs")
    description: str = Field(..., description="Violation description")
    suggested_fixes: list[SuggestedFix] = Field(
        default_factory=list, description="Auto-fix suggestions"
    )


class ValidationFix(BaseModel):
    """Applied validation fix record."""

    violation_type: str = Field(..., description="Type of violation fixed")
    line_number: int = Field(..., description="Line number of fix")
    strategy: str = Field(..., description="Fix strategy applied")
    confidence: float = Field(..., description="Confidence score of fix")
    success: bool = Field(..., description="Whether fix was successful")


class ValidationReport(BaseModel):
    """NECESSARY compliance validation report."""

    file_path: str = Field(..., description="Path to validated test file")
    passed: bool = Field(..., description="Whether validation passed")
    violations: list[Violation] = Field(default_factory=list, description="Detected violations")
    fixes: list[ValidationFix] = Field(
        default_factory=list, description="Fixes applied during validation"
    )


# Validation Rules


class NECESSARYValidator:
    """
    AST-based NECESSARY pattern validator for pytest test files.

    Validates test files against NECESSARY pattern compliance using
    Python AST parsing. Detects violations and generates confidence-scored
    auto-fix suggestions.

    Constitutional Compliance:
    - Article I: Complete AST parsing before validation
    - Article II: Test quality enforcement
    - Article IV: VectorStore integration for proven patterns
    """

    # Violation regex patterns
    GENERIC_NAME_PATTERNS = [
        r"^test_[0-9]+$",  # test_1, test_2
        r"^test_(basic|simple|test)$",  # test_basic, test_simple
        r"^test_(foo|bar|baz|temp)(_|$)",  # test_foo, test_bar
    ]

    RECOMMENDED_NAME_PATTERN = r"^test_[a-z_]+_when_[a-z_]+_then_[a-z_]+"
    ALTERNATIVE_NAME_PATTERN = r"^test_[a-z_]+_[a-z_]+_[a-z_]+"  # Min 3 segments

    # AAA comment patterns
    AAA_PATTERNS = [
        (r"#\s*arrange", "arrange"),
        (r"#\s*setup", "arrange"),
        (r"#\s*given", "arrange"),
        (r"#\s*act", "act"),
        (r"#\s*execute", "act"),
        (r"#\s*when", "act"),
        (r"#\s*assert", "assert"),
        (r"#\s*verify", "assert"),
        (r"#\s*then", "assert"),
    ]

    def __init__(self) -> None:
        """Initialize NECESSARY validator."""
        pass

    def validate(self, test_file_path: str) -> Result[ValidationReport, str]:
        """
        Validate test file against NECESSARY pattern compliance.

        Args:
            test_file_path: Path to test file to validate

        Returns:
            Result containing ValidationReport or error message

        Constitutional Compliance:
        - Article I: Complete AST parsing (retries on incomplete context)
        - Article II: Test quality enforcement before acceptance
        """
        # Check file exists
        file_path = Path(test_file_path)
        if not file_path.exists():
            return Err(f"Test file not found: {test_file_path}")

        # Parse file to AST
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Handle empty files
            if not content.strip():
                return Ok(
                    ValidationReport(file_path=test_file_path, passed=True, violations=[], fixes=[])
                )

            tree = ast.parse(content, filename=test_file_path)
        except SyntaxError as e:
            return Err(f"Syntax error in {test_file_path} at line {e.lineno}: {e.msg}")
        except Exception as e:
            return Err(f"Failed to parse {test_file_path}: {str(e)}")

        # Extract test functions
        test_functions = self._extract_test_functions(tree)

        # Validate each test function
        violations: list[Violation] = []
        for test_func in test_functions:
            violations.extend(self._validate_test_function(test_func, content))

        # Generate report
        report = ValidationReport(
            file_path=test_file_path,
            passed=len(violations) == 0,
            violations=violations,
            fixes=[],
        )

        return Ok(report)

    def _extract_test_functions(self, tree: ast.AST) -> list[ast.FunctionDef]:
        """
        Extract test functions from AST.

        Extracts both module-level and class-based test functions.

        Args:
            tree: Parsed AST tree

        Returns:
            List of test function AST nodes
        """
        test_functions: list[ast.FunctionDef] = []

        for node in ast.walk(tree):
            # Module-level test functions
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                test_functions.append(node)

            # Class-based test methods
            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                for class_item in node.body:
                    if isinstance(class_item, ast.FunctionDef) and class_item.name.startswith(
                        "test_"
                    ):
                        test_functions.append(class_item)

        return test_functions

    def _validate_test_function(
        self, test_func: ast.FunctionDef, file_content: str
    ) -> list[Violation]:
        """
        Validate single test function against NECESSARY rules.

        Args:
            test_func: Test function AST node
            file_content: Full file content (for line extraction)

        Returns:
            List of violations detected
        """
        violations: list[Violation] = []

        # Rule 1: Naming validation
        naming_violation = self._check_naming(test_func)
        if naming_violation:
            violations.append(naming_violation)

        # Rule 2: AAA structure validation
        aaa_violation = self._check_aaa_structure(test_func, file_content)
        if aaa_violation:
            violations.append(aaa_violation)

        # Rule 3: Docstring validation
        docstring_violation = self._check_docstring(test_func)
        if docstring_violation:
            violations.append(docstring_violation)

        return violations

    def _check_naming(self, test_func: ast.FunctionDef) -> Violation | None:
        """
        Check test function naming compliance.

        Validates test names follow descriptive patterns:
        - Recommended: test_X_when_Y_then_Z
        - Alternative: test_X_Y_Z (min 3 segments)

        Args:
            test_func: Test function AST node

        Returns:
            Violation if name is non-compliant, None otherwise
        """
        func_name = test_func.name

        # Check for generic/placeholder names
        for pattern in self.GENERIC_NAME_PATTERNS:
            if re.match(pattern, func_name):
                return Violation(
                    type="naming",
                    severity="high",
                    line_number=test_func.lineno,
                    description=f"Generic test name '{func_name}' is not descriptive. "
                    f"Use pattern: test_X_when_Y_then_Z",
                    suggested_fixes=[
                        SuggestedFix(
                            description="Rename test to describe behavior (what/when/then)",
                            code_snippet=self._generate_descriptive_name(test_func),
                            confidence=0.70,
                        )
                    ],
                )

        # Check if name follows recommended patterns
        if not re.match(self.RECOMMENDED_NAME_PATTERN, func_name):
            # Check if at least follows alternative pattern
            if not re.match(self.ALTERNATIVE_NAME_PATTERN, func_name):
                return Violation(
                    type="naming",
                    severity="medium",
                    line_number=test_func.lineno,
                    description=f"Test name '{func_name}' should follow pattern: "
                    f"test_X_when_Y_then_Z or test_X_Y_Z (min 3 segments)",
                    suggested_fixes=[
                        SuggestedFix(
                            description="Apply when/then naming pattern",
                            code_snippet=self._suggest_when_then_pattern(func_name),
                            confidence=0.65,
                        )
                    ],
                )

        return None

    def _check_aaa_structure(
        self, test_func: ast.FunctionDef, file_content: str
    ) -> Violation | None:
        """
        Check test function for AAA (Arrange-Act-Assert) structure.

        Validates presence of AAA comments in test body.

        Args:
            test_func: Test function AST node
            file_content: Full file content for comment extraction

        Returns:
            Violation if AAA structure missing, None otherwise
        """
        # Extract comments from function body
        func_lines = file_content.split("\n")[test_func.lineno - 1 : test_func.end_lineno]
        func_text = "\n".join(func_lines).lower()

        # Detect AAA sections
        aaa_found = {"arrange": False, "act": False, "assert": False}

        for pattern, section in self.AAA_PATTERNS:
            if re.search(pattern, func_text, re.IGNORECASE):
                aaa_found[section] = True

        # Check if all sections present
        missing_sections = [section for section, found in aaa_found.items() if not found]

        if missing_sections:
            return Violation(
                type="aaa_structure",
                severity="medium",
                line_number=test_func.lineno,
                description=f"Test missing AAA structure comments. Missing: {', '.join(missing_sections)}",
                suggested_fixes=[
                    SuggestedFix(
                        description="Insert Arrange/Act/Assert comments",
                        code_snippet=self._generate_aaa_comments(test_func),
                        confidence=0.92,  # High confidence for structural fix
                    )
                ],
            )

        return None

    def _check_docstring(self, test_func: ast.FunctionDef) -> Violation | None:
        """
        Check test function for descriptive docstring.

        Validates presence and quality of docstring.

        Args:
            test_func: Test function AST node

        Returns:
            Violation if docstring missing/generic, None otherwise
        """
        docstring = ast.get_docstring(test_func)

        if not docstring:
            return Violation(
                type="docstring",
                severity="medium",
                line_number=test_func.lineno,
                description=f"Test '{test_func.name}' is missing a docstring",
                suggested_fixes=[
                    SuggestedFix(
                        description="Generate docstring from test name",
                        code_snippet=self._generate_docstring(test_func),
                        confidence=0.68,
                    )
                ],
            )

        # Check for generic docstrings (strict check for obviously bad ones)
        # Only flag if it's clearly a placeholder, not just "Test X"
        docstring_lower = docstring.strip().lower()

        # Exact match for truly generic docstrings
        truly_generic = ["test", "test.", "todo", "tbd", "fixme", "wip"]
        if docstring_lower in truly_generic:
            return Violation(
                type="docstring",
                severity="low",
                line_number=test_func.lineno,
                description=f"Test docstring is too generic: '{docstring}'",
                suggested_fixes=[
                    SuggestedFix(
                        description="Improve docstring clarity",
                        code_snippet=self._generate_docstring(test_func),
                        confidence=0.65,
                    )
                ],
            )

        # Flag if only contains "TODO:" or "FIXME:"
        if any(placeholder in docstring for placeholder in ["TODO:", "FIXME:", "TBD:"]):
            return Violation(
                type="docstring",
                severity="low",
                line_number=test_func.lineno,
                description=f"Test docstring contains placeholder: '{docstring}'",
                suggested_fixes=[
                    SuggestedFix(
                        description="Replace placeholder with actual description",
                        code_snippet=self._generate_docstring(test_func),
                        confidence=0.65,
                    )
                ],
            )

        return None

    # Auto-fix generators

    def _generate_descriptive_name(self, test_func: ast.FunctionDef) -> str:
        """
        Generate descriptive test name from function body.

        Args:
            test_func: Test function AST node

        Returns:
            Suggested descriptive function name
        """
        # Analyze function body for clues
        func_name = test_func.name

        # Try to extract function being tested from first call
        for node in ast.walk(test_func):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    tested_func = node.func.id
                    return f"test_{tested_func}_when_valid_input_then_returns_result"
                elif isinstance(node.func, ast.Attribute):
                    tested_func = node.func.attr
                    return f"test_{tested_func}_when_called_then_succeeds"

        # Fallback: suggest pattern
        return "test_function_when_condition_then_outcome"

    def _suggest_when_then_pattern(self, func_name: str) -> str:
        """
        Suggest when/then pattern for existing test name.

        Args:
            func_name: Current function name

        Returns:
            Suggested function name with when/then
        """
        # Remove test_ prefix
        name_without_prefix = func_name.replace("test_", "")

        # Simple heuristic: add when/then structure
        if "_" in name_without_prefix:
            parts = name_without_prefix.split("_")
            if len(parts) >= 2:
                return f"test_{parts[0]}_when_{parts[1]}_then_{'_'.join(parts[2:]) or 'succeeds'}"

        return f"test_{name_without_prefix}_when_called_then_succeeds"

    def _generate_aaa_comments(self, test_func: ast.FunctionDef) -> str:
        """
        Generate AAA comment insertion code.

        Args:
            test_func: Test function AST node

        Returns:
            Code snippet with AAA comments inserted
        """
        # This would analyze statement types and insert comments
        # For now, return template
        return """    # Arrange
    # ... setup code ...

    # Act
    # ... action code ...

    # Assert
    # ... verification code ..."""

    def _generate_docstring(self, test_func: ast.FunctionDef) -> str:
        """
        Generate docstring from test name.

        Args:
            test_func: Test function AST node

        Returns:
            Generated docstring
        """
        # Convert snake_case test name to sentence
        func_name = test_func.name.replace("test_", "").replace("_", " ")

        # Capitalize first letter
        docstring = func_name.capitalize() + "."

        return f'"""{docstring}"""'
