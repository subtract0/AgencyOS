"""
Mars Rover Reliability - Phase 2: Autonomous Test Generator Tests.

Constitutional Compliance:
- Article VI: TDD (Tests written FIRST)
- Article VII: Value-First Testing (NECESSARY pattern)
- Article IV: Learning (stores gaps to backlog)

Acceptance Criteria:
1. Gap detection finds untested functions via AST
2. Test generation uses NECESSARY pattern
3. Generated tests follow AAA pattern
4. Failed tests stored to backlog
"""

import ast
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


class TestGapDetection:
    """Test coverage gap detection tests."""

    def test_detects_untested_functions(self) -> None:
        """Should detect functions without test coverage."""
        from tools.mars_rover.test_generator import (
            CoverageGap,
            TestGapDetector,
        )

        detector = TestGapDetector()

        # Sample Python code with untested function
        sample_code = '''
def calculate_total(items):
    """Calculate total of items."""
    return sum(items)

def validate_input(data):
    """Validate input data."""
    return bool(data)
'''

        # Sample test code that only tests calculate_total
        test_code = '''
def test_calculate_total():
    from module import calculate_total
    assert calculate_total([1, 2, 3]) == 6
'''

        gaps = detector.find_gaps(
            source_code=sample_code,
            test_code=test_code,
            module_name="sample_module",
        )

        assert len(gaps) > 0, "Should detect at least one gap"
        gap_names = [g.function_name for g in gaps]
        assert "validate_input" in gap_names, "Should detect untested validate_input"

    def test_detects_classes_without_tests(self) -> None:
        """Should detect classes without test coverage."""
        from tools.mars_rover.test_generator import TestGapDetector

        detector = TestGapDetector()

        sample_code = '''
class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b
'''

        test_code = '''
def test_calculator_add():
    calc = Calculator()
    assert calc.add(1, 2) == 3
'''

        gaps = detector.find_gaps(
            source_code=sample_code,
            test_code=test_code,
            module_name="calculator",
        )

        # Should detect subtract method as untested
        gap_names = [g.function_name for g in gaps]
        assert "Calculator.subtract" in gap_names or "subtract" in gap_names

    def test_uses_ast_for_detection(self) -> None:
        """Should use AST parsing for accurate detection."""
        from tools.mars_rover.test_generator import TestGapDetector

        detector = TestGapDetector()

        # Code with nested functions and edge cases
        sample_code = '''
def outer_function():
    def inner_function():
        pass
    return inner_function()

async def async_function():
    pass
'''

        gaps = detector.find_gaps(
            source_code=sample_code,
            test_code="",
            module_name="nested",
        )

        # Should detect outer function
        gap_names = [g.function_name for g in gaps]
        assert "outer_function" in gap_names


class TestNECESSARYPattern:
    """NECESSARY pattern test generation tests."""

    def test_generates_normal_path_tests(self) -> None:
        """Should generate Normal path tests (happy path)."""
        from tools.mars_rover.test_generator import NECESSARYGenerator

        generator = NECESSARYGenerator()

        function_info = {
            "name": "calculate_sum",
            "args": ["numbers"],
            "return_type": "int",
            "docstring": "Calculate sum of numbers.",
        }

        tests = generator.generate_tests(function_info)

        assert any("normal" in t.category.lower() for t in tests), (
            "Should generate Normal path test"
        )

    def test_generates_edge_case_tests(self) -> None:
        """Should generate Edge case tests."""
        from tools.mars_rover.test_generator import NECESSARYGenerator

        generator = NECESSARYGenerator()

        function_info = {
            "name": "divide",
            "args": ["a", "b"],
            "return_type": "float",
            "docstring": "Divide a by b.",
        }

        tests = generator.generate_tests(function_info)

        assert any("edge" in t.category.lower() for t in tests), (
            "Should generate Edge case test"
        )

    def test_generates_security_tests(self) -> None:
        """Should generate Security tests for sensitive functions."""
        from tools.mars_rover.test_generator import NECESSARYGenerator

        generator = NECESSARYGenerator()

        # Function that handles user input
        function_info = {
            "name": "process_user_input",
            "args": ["user_data"],
            "return_type": "str",
            "docstring": "Process user input data.",
        }

        tests = generator.generate_tests(function_info)

        assert any("security" in t.category.lower() for t in tests), (
            "Should generate Security test for user input function"
        )


class TestAAAPattern:
    """AAA (Arrange-Act-Assert) pattern tests."""

    def test_generated_tests_follow_aaa(self) -> None:
        """Generated tests should follow AAA pattern."""
        from tools.mars_rover.test_generator import NECESSARYGenerator

        generator = NECESSARYGenerator()

        function_info = {
            "name": "add_numbers",
            "args": ["a", "b"],
            "return_type": "int",
            "docstring": "Add two numbers.",
        }

        tests = generator.generate_tests(function_info)

        for test in tests:
            # Check for AAA sections in test code
            code = test.code
            assert "# Arrange" in code or "arrange" in code.lower(), (
                f"Test {test.name} missing Arrange section"
            )
            assert "# Act" in code or "result" in code.lower(), (
                f"Test {test.name} missing Act section"
            )
            assert "assert" in code.lower(), (
                f"Test {test.name} missing Assert section"
            )


class TestBacklogStorage:
    """Backlog storage tests."""

    def test_stores_gaps_to_backlog(self) -> None:
        """Should store coverage gaps to backlog."""
        from tools.mars_rover.test_generator import TestGapBacklog

        with tempfile.TemporaryDirectory() as temp_dir:
            backlog = TestGapBacklog(backlog_dir=temp_dir)

            gap_info = {
                "module": "example_module",
                "function": "untested_function",
                "priority": "high",
                "reason": "No test coverage",
            }

            backlog.store_gap(gap_info)

            # Verify gap was stored
            gaps = backlog.get_all_gaps()
            assert len(gaps) > 0, "Gap should be stored"
            assert gaps[0]["function"] == "untested_function"

    def test_marks_gaps_as_resolved(self) -> None:
        """Should mark gaps as resolved when tests are added."""
        from tools.mars_rover.test_generator import TestGapBacklog

        with tempfile.TemporaryDirectory() as temp_dir:
            backlog = TestGapBacklog(backlog_dir=temp_dir)

            gap_info = {
                "module": "example_module",
                "function": "now_tested_function",
                "priority": "medium",
            }

            gap_id = backlog.store_gap(gap_info)
            backlog.mark_resolved(gap_id)

            # Verify gap is marked resolved
            gaps = backlog.get_pending_gaps()
            assert all(g.get("function") != "now_tested_function" for g in gaps)


class TestEndToEndGeneration:
    """End-to-end test generation tests."""

    def test_full_generation_workflow(self) -> None:
        """Should complete full test generation workflow."""
        from tools.mars_rover.test_generator import AutonomousTestGenerator

        generator = AutonomousTestGenerator()

        sample_code = '''
def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}!"
'''

        result = generator.generate_for_code(
            source_code=sample_code,
            module_name="greeting",
        )

        assert result.success, f"Generation should succeed: {result.message}"
        assert len(result.generated_tests) > 0, "Should generate tests"

    def test_handles_complex_functions(self) -> None:
        """Should handle complex functions with type hints."""
        from tools.mars_rover.test_generator import AutonomousTestGenerator

        generator = AutonomousTestGenerator()

        sample_code = '''
from typing import List, Optional

def process_items(
    items: List[str],
    filter_fn: Optional[callable] = None,
    max_items: int = 100,
) -> List[str]:
    """Process a list of items with optional filtering."""
    if filter_fn:
        items = [x for x in items if filter_fn(x)]
    return items[:max_items]
'''

        result = generator.generate_for_code(
            source_code=sample_code,
            module_name="processor",
        )

        assert result.success, "Should handle complex functions"


class TestGeneratorConfiguration:
    """Configuration tests."""

    def test_default_configuration(self) -> None:
        """Default configuration should have sensible values."""
        from tools.mars_rover.test_generator import TestGeneratorConfig

        config = TestGeneratorConfig()

        assert config.min_tests_per_function > 0
        assert config.include_security_tests
        assert config.aaa_pattern_required

    def test_configurable_patterns(self) -> None:
        """Should allow configuring which NECESSARY patterns to use."""
        from tools.mars_rover.test_generator import (
            NECESSARYGenerator,
            TestGeneratorConfig,
        )

        config = TestGeneratorConfig(
            necessary_patterns=["Normal", "Edge"],  # No Security
        )

        generator = NECESSARYGenerator(config)

        function_info = {
            "name": "example",
            "args": ["data"],
            "return_type": "str",
        }

        tests = generator.generate_tests(function_info)
        categories = [t.category for t in tests]

        assert "Security" not in categories, "Should exclude Security per config"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
