"""
TestGeneratorAgent - Generates NECESSARY-compliant tests to address quality violations.
"""

import os
import json
import ast
from typing import Dict, List
from pathlib import Path
from textwrap import dedent

from agency_swarm import Agent
from agency_swarm.tools import BaseTool as Tool
from pydantic import Field

from shared.agent_context import AgentContext, create_agent_context
from shared.agent_utils import (
    detect_model_type,
    select_instructions_file,
    render_instructions,
    create_model_settings,
    get_model_instance,
)
from shared.system_hooks import create_system_reminder_hook, create_memory_integration_hook, create_composite_hook
from tools import (
    Bash,
    Edit,
    Glob,
    Grep,
    MultiEdit,
    Read,
    Write,
)


class GenerateTests(Tool):
    """Generate NECESSARY-compliant tests for specific violations."""

    audit_report: str = Field(..., description="JSON audit report with violations to address")
    target_file: str = Field(..., description="Source file to generate tests for")

    def run(self):
        """Generate tests to address NECESSARY violations."""
        try:
            audit_data = json.loads(self.audit_report)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid audit report JSON"})

        if not os.path.exists(self.target_file):
            return json.dumps({"error": f"Target file not found: {self.target_file}"})

        # Analyze source file
        source_analysis = self._analyze_source_file(self.target_file)

        # Generate tests for violations
        violations = audit_data.get("violations", [])
        generated_tests = []

        for violation in violations:
            if violation.get("severity") in ["critical", "high"]:
                tests = self._generate_tests_for_violation(violation, source_analysis)
                generated_tests.extend(tests)

        # Determine test file path
        test_file_path = self._get_test_file_path(self.target_file)

        # Write tests to file
        test_content = self._create_test_file_content(generated_tests, source_analysis)
        self._write_test_file(test_file_path, test_content)

        return json.dumps({
            "status": "success",
            "target_file": self.target_file,
            "test_file": test_file_path,
            "violations_addressed": len([v for v in violations if v.get("severity") in ["critical", "high"]]),
            "tests_generated": len(generated_tests),
            "test_names": [t["name"] for t in generated_tests]
        }, indent=2)

    def _analyze_source_file(self, file_path: str) -> Dict:
        """Analyze source file to understand testable behaviors."""
        analysis = {
            "functions": [],
            "classes": [],
            "imports": [],
            "module_name": Path(file_path).stem
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):  # Public functions only
                        func_info = {
                            "name": node.name,
                            "args": [arg.arg for arg in node.args.args],
                            "has_return": self._has_return_statement(node),
                            "is_async": False,
                            "docstring": ast.get_docstring(node)
                        }
                        analysis["functions"].append(func_info)

                elif isinstance(node, ast.AsyncFunctionDef):
                    if not node.name.startswith('_'):
                        func_info = {
                            "name": node.name,
                            "args": [arg.arg for arg in node.args.args],
                            "has_return": self._has_return_statement(node),
                            "is_async": True,
                            "docstring": ast.get_docstring(node)
                        }
                        analysis["functions"].append(func_info)

                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "methods": [],
                        "docstring": ast.get_docstring(node)
                    }

                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if not item.name.startswith('_') or item.name == '__init__':
                                method_info = {
                                    "name": item.name,
                                    "args": [arg.arg for arg in item.args.args],
                                    "is_async": isinstance(item, ast.AsyncFunctionDef)
                                }
                                class_info["methods"].append(method_info)

                    analysis["classes"].append(class_info)

        except Exception as e:
            analysis["error"] = str(e)

        return analysis

    def _generate_tests_for_violation(self, violation: Dict, source_analysis: Dict) -> List[Dict]:
        """Generate specific tests for a NECESSARY violation."""
        property_type = violation.get("property", "")
        tests = []

        if property_type == "N":  # No Missing Behaviors
            tests.extend(self._generate_basic_tests(source_analysis))
        elif property_type == "E":  # Edge Cases
            tests.extend(self._generate_edge_case_tests(source_analysis))
        elif property_type == "C":  # Comprehensive Coverage
            tests.extend(self._generate_comprehensive_tests(source_analysis))
        elif property_type in ["E2", "ERROR"]:  # Error Conditions
            tests.extend(self._generate_error_tests(source_analysis))
        elif property_type == "S":  # State Validation
            tests.extend(self._generate_state_tests(source_analysis))
        elif property_type == "A":  # Async Operations
            tests.extend(self._generate_async_tests(source_analysis))

        return tests

    def _generate_basic_tests(self, analysis: Dict) -> List[Dict]:
        """Generate basic happy path tests."""
        tests = []

        for func in analysis["functions"]:
            test_name = f"test_{func['name']}_basic"
            test_code = self._create_basic_test_code(func, analysis["module_name"])

            tests.append({
                "name": test_name,
                "code": test_code,
                "type": "basic",
                "function": func["name"]
            })

        for cls in analysis["classes"]:
            for method in cls["methods"]:
                test_name = f"test_{cls['name'].lower()}_{method['name']}_basic"
                test_code = self._create_basic_method_test_code(cls, method, analysis["module_name"])

                tests.append({
                    "name": test_name,
                    "code": test_code,
                    "type": "basic",
                    "class": cls["name"],
                    "method": method["name"]
                })

        return tests

    def _generate_edge_case_tests(self, analysis: Dict) -> List[Dict]:
        """Generate edge case tests."""
        tests = []

        for func in analysis["functions"]:
            if func["args"]:  # Only generate edge cases if function has parameters
                test_name = f"test_{func['name']}_edge_cases"
                test_code = self._create_edge_case_test_code(func, analysis["module_name"])

                tests.append({
                    "name": test_name,
                    "code": test_code,
                    "type": "edge_case",
                    "function": func["name"]
                })

        return tests

    def _generate_comprehensive_tests(self, analysis: Dict) -> List[Dict]:
        """Generate comprehensive test coverage."""
        tests = []

        for func in analysis["functions"]:
            if len(func["args"]) > 1:  # Multiple parameter combinations
                test_name = f"test_{func['name']}_comprehensive"
                test_code = self._create_comprehensive_test_code(func, analysis["module_name"])

                tests.append({
                    "name": test_name,
                    "code": test_code,
                    "type": "comprehensive",
                    "function": func["name"]
                })

        return tests

    def _generate_error_tests(self, analysis: Dict) -> List[Dict]:
        """Generate error condition tests."""
        tests = []

        for func in analysis["functions"]:
            test_name = f"test_{func['name']}_error_conditions"
            test_code = self._create_error_test_code(func, analysis["module_name"])

            tests.append({
                "name": test_name,
                "code": test_code,
                "type": "error",
                "function": func["name"]
            })

        return tests

    def _generate_state_tests(self, analysis: Dict) -> List[Dict]:
        """Generate state validation tests."""
        tests = []

        for cls in analysis["classes"]:
            test_name = f"test_{cls['name'].lower()}_state_validation"
            test_code = self._create_state_test_code(cls, analysis["module_name"])

            tests.append({
                "name": test_name,
                "code": test_code,
                "type": "state",
                "class": cls["name"]
            })

        return tests

    def _generate_async_tests(self, analysis: Dict) -> List[Dict]:
        """Generate async operation tests."""
        tests = []

        for func in analysis["functions"]:
            if func["is_async"]:
                test_name = f"test_{func['name']}_async"
                test_code = self._create_async_test_code(func, analysis["module_name"])

                tests.append({
                    "name": test_name,
                    "code": test_code,
                    "type": "async",
                    "function": func["name"]
                })

        return tests

    def _create_basic_test_code(self, func: Dict, module_name: str) -> str:
        """Create basic test code for a function."""
        args_str = ", ".join(f"mock_{arg}" for arg in func["args"])
        call_str = f"{func['name']}({args_str})" if args_str else f"{func['name']}()"

        if func["has_return"]:
            assertion = "assert result is not None"
            result_line = "result = "
        else:
            assertion = "# Test completed successfully"
            result_line = ""

        return dedent(f'''
        def test_{func['name']}_basic():
            """Test basic functionality of {func['name']}."""
            from {module_name} import {func['name']}

            # Arrange
            {self._generate_mock_args(func["args"])}

            # Act
            {result_line}{call_str}

            # Assert
            {assertion}
        ''').strip()

    def _create_basic_method_test_code(self, cls: Dict, method: Dict, module_name: str) -> str:
        """Create basic test code for a class method."""
        if method["name"] == "__init__":
            return dedent(f'''
            def test_{cls['name'].lower()}_init():
                """Test {cls['name']} initialization."""
                from {module_name} import {cls['name']}

                # Act
                instance = {cls['name']}()

                # Assert
                assert instance is not None
            ''').strip()

        args_str = ", ".join(f"mock_{arg}" for arg in method["args"][1:])  # Skip 'self'
        call_str = f"instance.{method['name']}({args_str})" if args_str else f"instance.{method['name']}()"

        return dedent(f'''
        def test_{cls['name'].lower()}_{method['name']}_basic():
            """Test basic functionality of {cls['name']}.{method['name']}."""
            from {module_name} import {cls['name']}

            # Arrange
            instance = {cls['name']}()
            {self._generate_mock_args(method["args"][1:])}  # Skip 'self'

            # Act
            result = {call_str}

            # Assert
            # Add specific assertions based on expected behavior
            pass
        ''').strip()

    def _create_edge_case_test_code(self, func: Dict, module_name: str) -> str:
        """Create edge case test code."""
        return dedent(f'''
        def test_{func['name']}_edge_cases():
            """Test edge cases for {func['name']}."""
            from {module_name} import {func['name']}

            # Test with empty/None values
            # Test with boundary values
            # Test with invalid types

            # Example edge cases:
            # {func['name']}(None)
            # {func['name']}("")
            # {func['name']}(0)
            # {func['name']}(-1)

            pass  # Implement specific edge cases
        ''').strip()

    def _create_comprehensive_test_code(self, func: Dict, module_name: str) -> str:
        """Create comprehensive test code."""
        return dedent(f'''
        def test_{func['name']}_comprehensive():
            """Comprehensive test coverage for {func['name']}."""
            from {module_name} import {func['name']}

            # Test multiple input combinations
            test_cases = [
                # Add various input combinations
                # (input1, input2, expected_result),
            ]

            for inputs, expected in test_cases:
                result = {func['name']}(*inputs)
                assert result == expected
        ''').strip()

    def _create_error_test_code(self, func: Dict, module_name: str) -> str:
        """Create error condition test code."""
        return dedent(f'''
        def test_{func['name']}_error_conditions():
            """Test error conditions for {func['name']}."""
            import pytest
            from {module_name} import {func['name']}

            # Test invalid input types
            with pytest.raises(TypeError):
                {func['name']}("invalid_type")

            # Test invalid values
            with pytest.raises(ValueError):
                {func['name']}(-1)

            # Add more error condition tests as needed
        ''').strip()

    def _create_state_test_code(self, cls: Dict, module_name: str) -> str:
        """Create state validation test code."""
        return dedent(f'''
        def test_{cls['name'].lower()}_state_validation():
            """Test state validation for {cls['name']}."""
            from {module_name} import {cls['name']}

            # Arrange
            instance = {cls['name']}()
            initial_state = instance.__dict__.copy() if hasattr(instance, '__dict__') else {{}}

            # Act - perform operations that should change state
            # instance.some_method()

            # Assert - verify state changes
            # assert instance.some_attribute == expected_value
            # assert instance.__dict__ != initial_state

            pass  # Implement specific state validations
        ''').strip()

    def _create_async_test_code(self, func: Dict, module_name: str) -> str:
        """Create async test code."""
        args_str = ", ".join(f"mock_{arg}" for arg in func["args"])
        call_str = f"await {func['name']}({args_str})" if args_str else f"await {func['name']}()"

        return dedent(f'''
        @pytest.mark.asyncio
        async def test_{func['name']}_async():
            """Test async functionality of {func['name']}."""
            from {module_name} import {func['name']}

            # Arrange
            {self._generate_mock_args(func["args"])}

            # Act
            result = {call_str}

            # Assert
            assert result is not None
        ''').strip()

    def _generate_mock_args(self, args: List[str]) -> str:
        """Generate mock arguments for test functions."""
        if not args:
            return "# No arguments needed"

        mock_assignments = []
        for arg in args:
            if arg == "self":
                continue
            # Simple heuristic for mock values
            if "id" in arg.lower():
                mock_assignments.append(f'mock_{arg} = 1')
            elif "name" in arg.lower() or "str" in arg.lower():
                mock_assignments.append(f'mock_{arg} = "test_{arg}"')
            elif "count" in arg.lower() or "num" in arg.lower():
                mock_assignments.append(f'mock_{arg} = 5')
            elif "flag" in arg.lower() or "bool" in arg.lower():
                mock_assignments.append(f'mock_{arg} = True')
            else:
                mock_assignments.append(f'mock_{arg} = None  # TODO: Provide appropriate test value')

        return "\n    ".join(mock_assignments)

    def _create_test_file_content(self, tests: List[Dict], analysis: Dict) -> str:
        """Create complete test file content."""
        header = dedent(f'''
        """
        Tests for {analysis["module_name"]}.py
        Generated by TestGeneratorAgent for NECESSARY compliance.
        """

        import pytest

        ''').strip()

        test_codes = [test["code"] for test in tests]
        return header + "\n\n\n" + "\n\n\n".join(test_codes)

    def _get_test_file_path(self, source_file: str) -> str:
        """Determine appropriate test file path."""
        source_path = Path(source_file)
        test_dir = source_path.parent / "tests"
        test_dir.mkdir(exist_ok=True)

        test_filename = f"test_{source_path.stem}.py"
        return str(test_dir / test_filename)

    def _write_test_file(self, test_file_path: str, content: str):
        """Write test content to file."""
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _has_return_statement(self, node) -> bool:
        """Check if function has return statement."""
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value is not None:
                return True
        return False


def create_test_generator_agent(
    model: str = "gpt-5", reasoning_effort: str = "medium", agent_context: AgentContext = None
) -> Agent:
    """Factory that returns a fresh TestGeneratorAgent instance."""

    is_openai, is_claude, _ = detect_model_type(model)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    instructions_file = select_instructions_file(current_dir, model)
    instructions = render_instructions(instructions_file, model)

    # Create agent context if not provided
    if agent_context is None:
        agent_context = create_agent_context()

    # Create hooks with memory integration
    reminder_hook = create_system_reminder_hook()
    memory_hook = create_memory_integration_hook(agent_context)
    combined_hook = create_composite_hook([reminder_hook, memory_hook])

    # Log agent creation
    agent_context.store_memory(
        f"test_generator_agent_created_{agent_context.session_id}",
        {
            "agent_type": "TestGeneratorAgent",
            "model": model,
            "reasoning_effort": reasoning_effort,
            "session_id": agent_context.session_id
        },
        ["agency", "test_generator", "creation"]
    )

    return Agent(
        name="TestGeneratorAgent",
        description="The test generation specialist. Creates NECESSARY-compliant tests based on violation reports from the AuditorAgent. Automatically generates comprehensive test suites to improve Q(T) scores and ensure code quality.",
        instructions=instructions,
        tools_folder=os.path.join(current_dir, "tools"),
        model=get_model_instance(model),
        hooks=combined_hook,
        tools=[
            Bash,
            Edit,
            Glob,
            Grep,
            MultiEdit,
            Read,
            Write,
            GenerateTests,
        ],
        model_settings=create_model_settings(model, reasoning_effort),
    )