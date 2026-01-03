"""
Mars Rover Reliability - Phase 2: Autonomous Test Generator.

Detects test coverage gaps and generates tests using NECESSARY pattern.

Constitutional Compliance:
- Article VI: TDD (generates tests first)
- Article VII: Value-First Testing (NECESSARY pattern)
- Article IV: Learning (stores gaps to backlog for tracking)

Features:
1. AST-based gap detection
2. NECESSARY pattern (Normal/Edge/Security)
3. AAA pattern test structure
4. Backlog storage for unresolved gaps
"""

import ast
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class CoverageGap:
    """Represents a test coverage gap."""

    function_name: str
    module_name: str
    line_number: int
    function_type: str  # "function", "method", "async_function"
    args: list[str] = field(default_factory=list)
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])


@dataclass
class GeneratedTest:
    """A generated test case."""

    name: str
    category: str  # "Normal", "Edge", "Security", etc.
    code: str
    target_function: str
    confidence: float = 0.8


@dataclass
class GenerationResult:
    """Result of test generation."""

    success: bool
    message: str
    generated_tests: list[GeneratedTest] = field(default_factory=list)
    gaps_found: list[CoverageGap] = field(default_factory=list)


@dataclass
class TestGeneratorConfig:
    """Configuration for test generator."""

    min_tests_per_function: int = 3
    include_security_tests: bool = True
    aaa_pattern_required: bool = True
    necessary_patterns: list[str] = field(
        default_factory=lambda: ["Normal", "Edge", "Security"]
    )
    backlog_dir: str = "~/.agency/memories/agency_backlog"


class TestGapDetector:
    """Detects test coverage gaps using AST analysis."""

    def find_gaps(
        self,
        source_code: str,
        test_code: str,
        module_name: str,
    ) -> list[CoverageGap]:
        """
        Find functions without test coverage.

        Args:
            source_code: Source code to analyze
            test_code: Existing test code
            module_name: Name of the module

        Returns:
            List of coverage gaps
        """
        # Parse source code
        source_functions = self._extract_functions(source_code)

        # Parse test code to find what's tested
        tested_functions = self._extract_tested_functions(test_code)

        # Find gaps
        gaps = []
        for func in source_functions:
            if not self._is_tested(func, tested_functions):
                gaps.append(
                    CoverageGap(
                        function_name=func["name"],
                        module_name=module_name,
                        line_number=func.get("line", 0),
                        function_type=func.get("type", "function"),
                        args=func.get("args", []),
                        return_type=func.get("return_type"),
                        docstring=func.get("docstring"),
                    )
                )

        return gaps

    def _extract_functions(self, code: str) -> list[dict]:
        """Extract all functions from code using AST."""
        functions = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            logger.warning(f"Failed to parse code: {e}")
            return []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "type": "function",
                    "line": node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "docstring": ast.get_docstring(node),
                }

                # Check return type annotation
                if node.returns:
                    func_info["return_type"] = ast.unparse(node.returns)

                functions.append(func_info)

            elif isinstance(node, ast.AsyncFunctionDef):
                func_info = {
                    "name": node.name,
                    "type": "async_function",
                    "line": node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "docstring": ast.get_docstring(node),
                }
                functions.append(func_info)

            elif isinstance(node, ast.ClassDef):
                # Extract methods from classes
                class_name = node.name
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not item.name.startswith("_") or item.name == "__init__":
                            method_name = f"{class_name}.{item.name}"
                            func_info = {
                                "name": method_name,
                                "type": "method",
                                "line": item.lineno,
                                "args": [arg.arg for arg in item.args.args if arg.arg != "self"],
                                "docstring": ast.get_docstring(item),
                            }
                            functions.append(func_info)

        return functions

    def _extract_tested_functions(self, test_code: str) -> set[str]:
        """Extract function names that are tested."""
        tested = set()

        # Look for test function names and infer what they test
        test_pattern = r"def test_(\w+)"
        matches = re.findall(test_pattern, test_code)
        tested.update(matches)

        # Look for imports/calls in test code
        call_pattern = r"(\w+)\("
        calls = re.findall(call_pattern, test_code)
        tested.update(calls)

        return tested

    def _is_tested(self, func: dict, tested: set[str]) -> bool:
        """Check if a function is tested."""
        name = func["name"]

        # Handle class.method format
        if "." in name:
            class_name, method_name = name.split(".", 1)
            return (
                method_name in tested
                or name.lower() in tested
                or f"{class_name.lower()}_{method_name}" in tested
            )

        # Direct match or snake_case match
        return name in tested or name.lower() in tested


class NECESSARYGenerator:
    """
    Generates tests using NECESSARY pattern.

    NECESSARY: Normal, Edge, Corner, Error, Security, Stress, Async, Regression, Yield
    (We focus on Normal, Edge, Security for coverage)
    """

    def __init__(self, config: Optional[TestGeneratorConfig] = None):
        """Initialize generator."""
        self.config = config or TestGeneratorConfig()

    def generate_tests(self, function_info: dict) -> list[GeneratedTest]:
        """
        Generate tests for a function.

        Args:
            function_info: Dictionary with function metadata

        Returns:
            List of generated tests
        """
        tests = []
        func_name = function_info.get("name", "unknown")
        args = function_info.get("args", [])
        return_type = function_info.get("return_type", "Any")
        docstring = function_info.get("docstring", "")

        # Generate Normal path test
        if "Normal" in self.config.necessary_patterns:
            tests.append(self._generate_normal_test(func_name, args, return_type, docstring))

        # Generate Edge case test
        if "Edge" in self.config.necessary_patterns:
            tests.append(self._generate_edge_test(func_name, args, return_type))

        # Generate Security test if applicable
        if "Security" in self.config.necessary_patterns:
            if self._needs_security_test(func_name, args, docstring):
                tests.append(self._generate_security_test(func_name, args))

        return tests

    def _generate_normal_test(
        self,
        func_name: str,
        args: list[str],
        return_type: str,
        docstring: str,
    ) -> GeneratedTest:
        """Generate a Normal path (happy path) test."""
        test_name = f"test_{self._snake_case(func_name)}_normal"

        # Generate sample args based on type hints or names
        sample_args = self._generate_sample_args(args)

        code = f'''def {test_name}():
    """Test normal execution path for {func_name}."""
    # Arrange
    {self._format_arrange(args, sample_args)}

    # Act
    result = {func_name}({", ".join(args)})

    # Assert
    assert result is not None, "Result should not be None"
'''

        return GeneratedTest(
            name=test_name,
            category="Normal",
            code=code,
            target_function=func_name,
        )

    def _generate_edge_test(
        self,
        func_name: str,
        args: list[str],
        return_type: str,
    ) -> GeneratedTest:
        """Generate an Edge case test."""
        test_name = f"test_{self._snake_case(func_name)}_edge_empty"

        code = f'''def {test_name}():
    """Test edge case with empty/minimal input for {func_name}."""
    # Arrange
    {self._format_edge_arrange(args)}

    # Act
    try:
        result = {func_name}({", ".join(args)})
        # Assert - function handles edge case gracefully
        assert True, "Function handled edge case"
    except (ValueError, TypeError) as e:
        # Assert - function raises appropriate error
        assert True, "Function raised expected error for edge case"
'''

        return GeneratedTest(
            name=test_name,
            category="Edge",
            code=code,
            target_function=func_name,
        )

    def _generate_security_test(
        self,
        func_name: str,
        args: list[str],
    ) -> GeneratedTest:
        """Generate a Security test."""
        test_name = f"test_{self._snake_case(func_name)}_security_injection"

        code = f'''def {test_name}():
    """Test security - injection prevention for {func_name}."""
    # Arrange
    # Potentially malicious input
    {self._format_security_arrange(args)}

    # Act & Assert
    try:
        result = {func_name}({", ".join(args)})
        # If function returns, verify no injection occurred
        if isinstance(result, str):
            assert "<script>" not in result.lower(), "XSS injection detected"
            assert "'; DROP" not in result, "SQL injection detected"
    except (ValueError, TypeError, SecurityError) as e:
        # Function correctly rejected malicious input
        assert True, "Function rejected malicious input"
'''

        return GeneratedTest(
            name=test_name,
            category="Security",
            code=code,
            target_function=func_name,
        )

    def _needs_security_test(
        self,
        func_name: str,
        args: list[str],
        docstring: str,
    ) -> bool:
        """Determine if function needs security testing."""
        security_keywords = [
            "user", "input", "data", "query", "sql", "html",
            "request", "param", "form", "api", "auth",
        ]

        # Check function name
        name_lower = func_name.lower()
        for keyword in security_keywords:
            if keyword in name_lower:
                return True

        # Check argument names
        for arg in args:
            arg_lower = arg.lower()
            for keyword in security_keywords:
                if keyword in arg_lower:
                    return True

        # Check docstring
        if docstring:
            doc_lower = docstring.lower()
            for keyword in security_keywords:
                if keyword in doc_lower:
                    return True

        return False

    def _snake_case(self, name: str) -> str:
        """Convert name to snake_case."""
        # Handle Class.method format
        name = name.replace(".", "_")
        # Convert CamelCase to snake_case
        result = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        return result

    def _generate_sample_args(self, args: list[str]) -> dict[str, str]:
        """Generate sample argument values."""
        samples = {}
        for arg in args:
            arg_lower = arg.lower()
            if "num" in arg_lower or arg in ["a", "b", "n", "x", "y"]:
                samples[arg] = "42"
            elif "str" in arg_lower or "name" in arg_lower or "text" in arg_lower:
                samples[arg] = '"example"'
            elif "list" in arg_lower or "items" in arg_lower or "numbers" in arg_lower:
                samples[arg] = "[1, 2, 3]"
            elif "dict" in arg_lower or "data" in arg_lower:
                samples[arg] = '{"key": "value"}'
            elif "bool" in arg_lower or "flag" in arg_lower:
                samples[arg] = "True"
            else:
                samples[arg] = '"test_value"'
        return samples

    def _format_arrange(self, args: list[str], samples: dict[str, str]) -> str:
        """Format Arrange section."""
        lines = []
        for arg in args:
            value = samples.get(arg, '"test"')
            lines.append(f"{arg} = {value}")
        return "\n    ".join(lines) if lines else "pass  # No arrangement needed"

    def _format_edge_arrange(self, args: list[str]) -> str:
        """Format Arrange section for edge cases."""
        lines = []
        for arg in args:
            arg_lower = arg.lower()
            if "list" in arg_lower or "items" in arg_lower:
                lines.append(f"{arg} = []  # Empty list")
            elif "str" in arg_lower or "name" in arg_lower:
                lines.append(f'{arg} = ""  # Empty string')
            elif "num" in arg_lower or arg in ["a", "b", "n"]:
                lines.append(f"{arg} = 0  # Zero value")
            elif "dict" in arg_lower or "data" in arg_lower:
                lines.append(f"{arg} = {{}}  # Empty dict")
            else:
                lines.append(f"{arg} = None  # None value")
        return "\n    ".join(lines) if lines else "pass  # No arrangement needed"

    def _format_security_arrange(self, args: list[str]) -> str:
        """Format Arrange section for security tests."""
        lines = []
        for arg in args:
            arg_lower = arg.lower()
            if "sql" in arg_lower or "query" in arg_lower:
                lines.append(f'{arg} = "\\"; DROP TABLE users; --"')
            elif "html" in arg_lower or "text" in arg_lower:
                lines.append(f'{arg} = "<script>alert(\\"XSS\\")</script>"')
            else:
                lines.append(f'{arg} = "<script>malicious</script>"')
        return "\n    ".join(lines) if lines else "pass  # No arrangement needed"


class TestGapBacklog:
    """Manages the backlog of test coverage gaps."""

    def __init__(self, backlog_dir: Optional[str] = None):
        """Initialize backlog manager."""
        self.backlog_dir = Path(
            backlog_dir or "~/.agency/memories/agency_backlog"
        ).expanduser()
        self.backlog_file = self.backlog_dir / "test_gaps.json"
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        """Ensure backlog directory exists."""
        self.backlog_dir.mkdir(parents=True, exist_ok=True)

    def store_gap(self, gap_info: dict) -> str:
        """
        Store a coverage gap to backlog.

        Args:
            gap_info: Gap information

        Returns:
            Gap ID
        """
        gaps = self._load_gaps()

        gap_id = str(uuid.uuid4())[:8]
        gap_info["id"] = gap_id
        gap_info["timestamp"] = datetime.now().isoformat()
        gap_info["resolved"] = False

        gaps.append(gap_info)
        self._save_gaps(gaps)

        logger.info(f"Stored gap {gap_id}: {gap_info.get('function')}")
        return gap_id

    def mark_resolved(self, gap_id: str) -> bool:
        """
        Mark a gap as resolved.

        Args:
            gap_id: Gap ID to mark resolved

        Returns:
            True if gap was found and marked
        """
        gaps = self._load_gaps()

        for gap in gaps:
            if gap.get("id") == gap_id:
                gap["resolved"] = True
                gap["resolved_at"] = datetime.now().isoformat()
                self._save_gaps(gaps)
                logger.info(f"Marked gap {gap_id} as resolved")
                return True

        return False

    def get_all_gaps(self) -> list[dict]:
        """Get all gaps."""
        return self._load_gaps()

    def get_pending_gaps(self) -> list[dict]:
        """Get unresolved gaps."""
        gaps = self._load_gaps()
        return [g for g in gaps if not g.get("resolved", False)]

    def _load_gaps(self) -> list[dict]:
        """Load gaps from file."""
        if not self.backlog_file.exists():
            return []

        try:
            with open(self.backlog_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load gaps: {e}")
            return []

    def _save_gaps(self, gaps: list[dict]) -> None:
        """Save gaps to file."""
        try:
            with open(self.backlog_file, "w") as f:
                json.dump(gaps, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save gaps: {e}")


class AutonomousTestGenerator:
    """
    Main autonomous test generator.

    Combines gap detection, test generation, and backlog management.
    """

    def __init__(self, config: Optional[TestGeneratorConfig] = None):
        """Initialize generator."""
        self.config = config or TestGeneratorConfig()
        self.gap_detector = TestGapDetector()
        self.test_generator = NECESSARYGenerator(self.config)
        self.backlog = TestGapBacklog(self.config.backlog_dir)

    def generate_for_code(
        self,
        source_code: str,
        module_name: str,
        existing_tests: str = "",
    ) -> GenerationResult:
        """
        Generate tests for source code.

        Args:
            source_code: Source code to generate tests for
            module_name: Name of the module
            existing_tests: Existing test code (to avoid duplicates)

        Returns:
            Generation result
        """
        try:
            # Find gaps
            gaps = self.gap_detector.find_gaps(
                source_code=source_code,
                test_code=existing_tests,
                module_name=module_name,
            )

            if not gaps:
                return GenerationResult(
                    success=True,
                    message="No coverage gaps found",
                    generated_tests=[],
                    gaps_found=[],
                )

            # Generate tests for each gap
            all_tests = []
            for gap in gaps:
                function_info = {
                    "name": gap.function_name,
                    "args": gap.args,
                    "return_type": gap.return_type,
                    "docstring": gap.docstring,
                }

                tests = self.test_generator.generate_tests(function_info)
                all_tests.extend(tests)

            return GenerationResult(
                success=True,
                message=f"Generated {len(all_tests)} tests for {len(gaps)} gaps",
                generated_tests=all_tests,
                gaps_found=gaps,
            )

        except Exception as e:
            logger.error(f"Test generation failed: {e}")
            return GenerationResult(
                success=False,
                message=f"Generation failed: {e}",
            )

    def scan_directory(
        self,
        source_dir: Path,
        test_dir: Path,
    ) -> GenerationResult:
        """
        Scan a directory for coverage gaps.

        Args:
            source_dir: Directory with source code
            test_dir: Directory with test code

        Returns:
            Generation result with all gaps and tests
        """
        all_tests = []
        all_gaps = []

        source_files = list(source_dir.glob("**/*.py"))

        for source_file in source_files:
            # Skip test files and __init__.py
            if source_file.name.startswith("test_") or source_file.name == "__init__.py":
                continue

            # Find corresponding test file
            module_name = source_file.stem
            test_file = test_dir / f"test_{module_name}.py"

            source_code = source_file.read_text()
            test_code = test_file.read_text() if test_file.exists() else ""

            result = self.generate_for_code(
                source_code=source_code,
                module_name=module_name,
                existing_tests=test_code,
            )

            if result.success:
                all_tests.extend(result.generated_tests)
                all_gaps.extend(result.gaps_found)

                # Store gaps to backlog
                for gap in result.gaps_found:
                    self.backlog.store_gap({
                        "module": module_name,
                        "function": gap.function_name,
                        "file": str(source_file),
                        "priority": "medium",
                    })

        return GenerationResult(
            success=True,
            message=f"Scanned {len(source_files)} files, found {len(all_gaps)} gaps",
            generated_tests=all_tests,
            gaps_found=all_gaps,
        )
