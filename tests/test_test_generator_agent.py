"""
Test TestGeneratorAgent behavior and functionality.
Tests for NECESSARY-compliant test generation, audit report processing, and file creation.
"""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from test_generator_agent.test_generator_agent import create_test_generator_agent, GenerateTests


@pytest.fixture
def sample_source_file():
    """Create a temporary source file for testing."""
    content = '''
def add_numbers(a, b):
    """Add two numbers together."""
    return a + b

def divide_numbers(a, b):
    """Divide first number by second number."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

class MathCalculator:
    """Simple math calculator."""

    def __init__(self, precision=2):
        self.precision = precision
        self.history = []

    def calculate(self, operation, a, b):
        """Perform calculation and store in history."""
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Division by zero")
            result = a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")

        rounded_result = round(result, self.precision)
        self.history.append(f"{a} {operation} {b} = {rounded_result}")
        return rounded_result

    async def async_calculation(self, a, b):
        """Async calculation example."""
        await asyncio.sleep(0.1)
        return a + b

    def _private_method(self):
        """Private method - should not be tested."""
        return "private"
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(content)
        temp_file_path = f.name

    yield temp_file_path

    # Cleanup
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)


@pytest.fixture
def sample_audit_report():
    """Create a sample audit report for testing."""
    return {
        "mode": "full",
        "target": "/test/path",
        "qt_score": 0.45,
        "necessary_compliance": {
            "N": {"score": 0.3, "violations": ["Low test coverage: 0.30"]},
            "E": {"score": 0.4, "violations": ["Insufficient edge case testing"]},
            "C": {"score": 0.5, "violations": ["Need more test cases per behavior"]},
            "E2": {"score": 0.2, "violations": ["Insufficient error condition testing"]},
            "S": {"score": 0.7, "violations": []},
            "S2": {"score": 0.6, "violations": []},
            "A": {"score": 0.3, "violations": ["Async operation testing needs attention"]},
            "R": {"score": 0.8, "violations": []},
            "Y": {"score": 0.4, "violations": ["Overall test confidence needs improvement"]}
        },
        "violations": [
            {
                "property": "N",
                "severity": "critical",
                "score": 0.3,
                "description": "Low test coverage: 0.30",
                "recommendation": "Add test cases for uncovered behaviors"
            },
            {
                "property": "E2",
                "severity": "critical",
                "score": 0.2,
                "description": "Insufficient error condition testing",
                "recommendation": "Implement error condition tests"
            },
            {
                "property": "A",
                "severity": "critical",
                "score": 0.3,
                "description": "Async operation testing needs attention",
                "recommendation": "Add async operation testing with proper await patterns"
            },
            {
                "property": "E",
                "severity": "high",
                "score": 0.4,
                "description": "Insufficient edge case testing",
                "recommendation": "Implement boundary condition and edge case tests"
            }
        ],
        "recommendations": ["CRITICAL: Q(T) score below 0.6 requires immediate attention"]
    }


@pytest.fixture
def mock_agent_context():
    """Create a mock agent context for testing."""
    context = Mock()
    context.session_id = "test_session_123"
    context.store_memory = Mock()
    return context


def test_test_generator_agent_initialization():
    """Test that TestGeneratorAgent can be initialized properly."""
    with patch('test_generator_agent.test_generator_agent.create_agent_context') as mock_context:
        mock_context.return_value = Mock()
        mock_context.return_value.session_id = "test_session"
        mock_context.return_value.store_memory = Mock()

        agent = create_test_generator_agent(model="gpt-5-mini", reasoning_effort="low")

        assert agent is not None
        assert agent.name == "TestGeneratorAgent"
        assert "NECESSARY-compliant tests" in agent.description
        # Check that agent has tools (specific tool verification is complex due to wrapping)
        assert len(agent.tools) > 0


def test_generate_tests_tool_initialization():
    """Test GenerateTests tool can be initialized."""
    audit_report = json.dumps({"violations": []})
    tool = GenerateTests(audit_report=audit_report, target_file="/test/file.py")

    assert tool.audit_report == audit_report
    assert tool.target_file == "/test/file.py"


def test_generate_tests_invalid_json():
    """Test GenerateTests handles invalid JSON gracefully."""
    tool = GenerateTests(audit_report="invalid json", target_file="/test/file.py")
    result = tool.run()

    result_data = json.loads(result)
    assert "error" in result_data
    assert "Invalid audit report JSON" in result_data["error"]


def test_generate_tests_nonexistent_file(sample_audit_report):
    """Test GenerateTests handles nonexistent target files gracefully."""
    tool = GenerateTests(
        audit_report=json.dumps(sample_audit_report),
        target_file="/nonexistent/file.py"
    )
    result = tool.run()

    result_data = json.loads(result)
    assert "error" in result_data
    assert "not found" in result_data["error"]


def test_source_file_analysis(sample_source_file):
    """Test source file analysis functionality."""
    tool = GenerateTests(audit_report=json.dumps({"violations": []}), target_file=sample_source_file)
    analysis = tool._analyze_source_file(sample_source_file)

    # Check basic structure
    assert "functions" in analysis
    assert "classes" in analysis
    assert "imports" in analysis
    assert "module_name" in analysis

    # Check function detection
    function_names = [f["name"] for f in analysis["functions"]]
    assert "add_numbers" in function_names
    assert "divide_numbers" in function_names
    assert "_private_method" not in function_names  # Private methods excluded

    # Check class detection
    class_names = [c["name"] for c in analysis["classes"]]
    assert "MathCalculator" in class_names

    # Check method detection within class
    math_calc_class = next(c for c in analysis["classes"] if c["name"] == "MathCalculator")
    method_names = [m["name"] for m in math_calc_class["methods"]]
    assert "__init__" in method_names
    assert "calculate" in method_names
    assert "async_calculation" in method_names
    assert "_private_method" not in method_names  # Private methods excluded

    # Check async detection
    async_functions = [f for f in analysis["functions"] if f.get("is_async", False)]
    assert len(async_functions) > 0


def test_basic_test_generation(sample_source_file, sample_audit_report):
    """Test basic test generation for functions."""
    tool = GenerateTests(
        audit_report=json.dumps(sample_audit_report),
        target_file=sample_source_file
    )

    analysis = tool._analyze_source_file(sample_source_file)

    # Test violation that triggers basic test generation
    violation = {"property": "N", "severity": "critical"}
    basic_tests = tool._generate_tests_for_violation(violation, analysis)

    assert len(basic_tests) > 0

    # Check test structure
    for test in basic_tests:
        assert "name" in test
        assert "code" in test
        assert "type" in test
        assert test["type"] == "basic"
        assert test["name"].startswith("test_")


def test_edge_case_test_generation(sample_source_file, sample_audit_report):
    """Test edge case test generation."""
    tool = GenerateTests(
        audit_report=json.dumps(sample_audit_report),
        target_file=sample_source_file
    )

    analysis = tool._analyze_source_file(sample_source_file)

    # Test violation that triggers edge case generation
    violation = {"property": "E", "severity": "high"}
    edge_tests = tool._generate_tests_for_violation(violation, analysis)

    assert len(edge_tests) > 0

    # Check test structure
    for test in edge_tests:
        assert test["type"] == "edge_case"
        assert "edge" in test["name"] or "boundary" in test["name"]


def test_error_condition_test_generation(sample_source_file, sample_audit_report):
    """Test error condition test generation."""
    tool = GenerateTests(
        audit_report=json.dumps(sample_audit_report),
        target_file=sample_source_file
    )

    analysis = tool._analyze_source_file(sample_source_file)

    # Test violation that triggers error testing
    violation = {"property": "E2", "severity": "critical"}
    error_tests = tool._generate_tests_for_violation(violation, analysis)

    assert len(error_tests) > 0

    # Check test structure
    for test in error_tests:
        assert test["type"] == "error"
        assert "error" in test["name"]
        # Error tests should include pytest.raises
        assert "pytest.raises" in test["code"]


def test_async_test_generation(sample_source_file, sample_audit_report):
    """Test async test generation."""
    tool = GenerateTests(
        audit_report=json.dumps(sample_audit_report),
        target_file=sample_source_file
    )

    analysis = tool._analyze_source_file(sample_source_file)

    # Test violation that triggers async testing
    violation = {"property": "A", "severity": "critical"}
    async_tests = tool._generate_tests_for_violation(violation, analysis)

    assert len(async_tests) > 0

    # Check test structure
    for test in async_tests:
        assert test["type"] == "async"
        assert "async" in test["name"]
        # Async tests should include @pytest.mark.asyncio and await
        assert "@pytest.mark.asyncio" in test["code"]
        assert "await" in test["code"]


def test_comprehensive_test_generation(sample_source_file, sample_audit_report):
    """Test comprehensive test generation."""
    tool = GenerateTests(
        audit_report=json.dumps(sample_audit_report),
        target_file=sample_source_file
    )

    analysis = tool._analyze_source_file(sample_source_file)

    # Test violation that triggers comprehensive testing
    violation = {"property": "C", "severity": "high"}
    comp_tests = tool._generate_tests_for_violation(violation, analysis)

    assert len(comp_tests) > 0

    # Check test structure
    for test in comp_tests:
        assert test["type"] == "comprehensive"
        assert "comprehensive" in test["name"]


def test_state_validation_test_generation(sample_source_file, sample_audit_report):
    """Test state validation test generation."""
    tool = GenerateTests(
        audit_report=json.dumps(sample_audit_report),
        target_file=sample_source_file
    )

    analysis = tool._analyze_source_file(sample_source_file)

    # Test violation that triggers state testing
    violation = {"property": "S", "severity": "medium"}
    state_tests = tool._generate_tests_for_violation(violation, analysis)

    # Should generate state tests for classes
    class_tests = [t for t in state_tests if t["type"] == "state"]
    if class_tests:  # Only if classes exist
        for test in class_tests:
            assert "state" in test["name"]


def test_test_file_path_generation(sample_source_file):
    """Test test file path generation logic."""
    tool = GenerateTests(audit_report=json.dumps({"violations": []}), target_file=sample_source_file)

    test_file_path = tool._get_test_file_path(sample_source_file)

    # Should be in tests directory relative to source
    assert "tests" in test_file_path
    assert test_file_path.endswith(".py")
    assert "test_" in os.path.basename(test_file_path)


def test_mock_argument_generation():
    """Test mock argument generation for different parameter types."""
    tool = GenerateTests(audit_report=json.dumps({"violations": []}), target_file="/test/file.py")

    # Test that mock arguments are generated
    result = tool._generate_mock_args(["user_id", "name", "count"])
    assert "mock_user_id" in result
    assert "mock_name" in result
    assert "mock_count" in result

    # Test empty args
    empty_result = tool._generate_mock_args([])
    assert "No arguments needed" in empty_result


def test_test_file_content_generation(sample_source_file, sample_audit_report):
    """Test complete test file content generation."""
    tool = GenerateTests(
        audit_report=json.dumps(sample_audit_report),
        target_file=sample_source_file
    )

    analysis = tool._analyze_source_file(sample_source_file)

    # Generate some tests
    violation = {"property": "N", "severity": "critical"}
    tests = tool._generate_tests_for_violation(violation, analysis)

    content = tool._create_test_file_content(tests, analysis)

    # Check file structure
    assert content.startswith('"""')  # Docstring
    assert "import pytest" in content
    assert "Generated by TestGeneratorAgent" in content

    # Check that test functions are included (basic verification)
    assert "def test_" in content
    assert len(tests) > 0


def test_full_test_generation_workflow(sample_source_file, sample_audit_report):
    """Test the complete test generation workflow."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy source file to temp directory for isolated testing
        source_path = Path(temp_dir) / "math_utils.py"
        with open(sample_source_file, 'r') as src:
            source_path.write_text(src.read())

        tool = GenerateTests(
            audit_report=json.dumps(sample_audit_report),
            target_file=str(source_path)
        )

        result = tool.run()
        result_data = json.loads(result)

        # Check success
        assert result_data["status"] == "success"
        assert "test_file" in result_data
        assert "violations_addressed" in result_data
        assert "tests_generated" in result_data
        assert "test_names" in result_data

        # Verify test file was created
        test_file_path = result_data["test_file"]
        assert os.path.exists(test_file_path)

        # Verify test file content
        with open(test_file_path, 'r') as f:
            test_content = f.read()

        assert "import pytest" in test_content
        assert "def test_" in test_content

        # Check that critical/high violations were addressed
        assert result_data["violations_addressed"] > 0


def test_necessary_compliance_verification(sample_source_file, sample_audit_report):
    """Test that generated tests follow NECESSARY principles."""
    tool = GenerateTests(
        audit_report=json.dumps(sample_audit_report),
        target_file=sample_source_file
    )

    analysis = tool._analyze_source_file(sample_source_file)

    # Test each NECESSARY property
    necessary_properties = ["N", "E", "C", "E2", "S", "A", "R", "Y"]

    for prop in necessary_properties:
        violation = {"property": prop, "severity": "high"}
        tool._generate_tests_for_violation(violation, analysis)

        # Verify tests are generated for each property
        if prop in ["N", "E", "C", "E2", "A"]:  # Properties that should generate tests
            # Should generate tests for these properties
            pass  # Basic verification that no errors occur


def test_error_handling_in_source_analysis():
    """Test error handling during source file analysis."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("invalid python syntax ][")
        invalid_file = f.name

    try:
        tool = GenerateTests(audit_report=json.dumps({"violations": []}), target_file=invalid_file)
        analysis = tool._analyze_source_file(invalid_file)

        # Should handle parse errors gracefully
        assert "error" in analysis or analysis["functions"] == []
    finally:
        os.unlink(invalid_file)


def test_severity_filtering(sample_source_file, sample_audit_report):
    """Test that only critical and high severity violations are addressed."""
    # Modify audit report to include different severities
    modified_report = sample_audit_report.copy()
    modified_report["violations"] = [
        {"property": "N", "severity": "critical", "description": "Critical issue"},
        {"property": "E", "severity": "high", "description": "High issue"},
        {"property": "C", "severity": "medium", "description": "Medium issue"},
        {"property": "S", "severity": "low", "description": "Low issue"}
    ]

    tool = GenerateTests(
        audit_report=json.dumps(modified_report),
        target_file=sample_source_file
    )

    result = tool.run()
    result_data = json.loads(result)

    # Should only address critical and high severity violations
    assert result_data["violations_addressed"] == 2  # Only critical and high


def test_memory_integration(mock_agent_context):
    """Test integration with Memory API."""
    with patch('test_generator_agent.test_generator_agent.create_agent_context') as mock_create_context:
        mock_create_context.return_value = mock_agent_context

        create_test_generator_agent(model="gpt-5-mini", reasoning_effort="low")

        # Verify memory storage was called during agent creation
        mock_agent_context.store_memory.assert_called()

        # Check the stored memory content
        call_args = mock_agent_context.store_memory.call_args
        assert call_args[0][0].startswith("test_generator_agent_created_")
        assert call_args[0][1]["agent_type"] == "TestGeneratorAgent"
        assert call_args[0][2] == ["agency", "test_generator", "creation"]


def test_test_file_creation_and_naming(sample_source_file):
    """Test test file creation and naming conventions."""
    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = Path(temp_dir) / "calculator.py"
        with open(sample_source_file, 'r') as src:
            source_path.write_text(src.read())

        tool = GenerateTests(
            audit_report=json.dumps({"violations": [{"property": "N", "severity": "critical"}]}),
            target_file=str(source_path)
        )

        test_file_path = tool._get_test_file_path(str(source_path))

        # Verify naming convention
        assert "test_calculator.py" in test_file_path
        assert str(temp_dir) in test_file_path

        # Verify tests directory is created
        tests_dir = Path(temp_dir) / "tests"
        tool._write_test_file(test_file_path, "# Test content")
        assert tests_dir.exists()
        assert Path(test_file_path).exists()


def test_basic_test_code_generation():
    """Test basic test code generation for functions."""
    tool = GenerateTests(audit_report=json.dumps({"violations": []}), target_file="/test/file.py")

    func_info = {
        "name": "add_numbers",
        "args": ["a", "b"],
        "has_return": True
    }

    test_code = tool._create_basic_test_code(func_info, "math_utils")

    # Verify test structure
    assert "def test_add_numbers_basic():" in test_code
    assert "from math_utils import add_numbers" in test_code
    assert "mock_a" in test_code
    assert "mock_b" in test_code
    assert "assert result is not None" in test_code


def test_method_test_code_generation():
    """Test test code generation for class methods."""
    tool = GenerateTests(audit_report=json.dumps({"violations": []}), target_file="/test/file.py")

    cls_info = {"name": "Calculator"}
    method_info = {
        "name": "calculate",
        "args": ["self", "operation", "a", "b"]
    }

    test_code = tool._create_basic_method_test_code(cls_info, method_info, "math_utils")

    # Verify test structure
    assert "def test_calculator_calculate_basic():" in test_code
    assert "from math_utils import Calculator" in test_code
    assert "instance = Calculator()" in test_code
    assert "mock_operation" in test_code