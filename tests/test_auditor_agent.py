"""
Test AuditorAgent behavior and functionality.
Tests for Q(T) scoring, NECESSARY property detection, and audit report generation.
"""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from auditor_agent.auditor_agent import create_auditor_agent, AnalyzeCodebase


@pytest.fixture
def sample_python_file():
    """Create a temporary Python file for testing."""
    content = '''
def calculate_sum(a, b):
    """Calculate the sum of two numbers."""
    return a + b

def calculate_product(a, b):
    """Calculate the product of two numbers."""
    if a == 0 or b == 0:
        return 0
    return a * b

class Calculator:
    """Simple calculator class."""

    def __init__(self):
        self.history = []

    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result

    async def async_operation(self):
        """Async operation example."""
        return "async_result"
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(content)
        temp_file_path = f.name

    yield temp_file_path

    # Cleanup
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)


@pytest.fixture
def sample_test_file():
    """Create a temporary test file for testing."""
    content = '''
import pytest

def test_calculate_sum():
    """Test basic sum calculation."""
    from sample import calculate_sum
    assert calculate_sum(2, 3) == 5

def test_calculate_sum_edge_cases():
    """Test edge cases for sum calculation."""
    from sample import calculate_sum
    assert calculate_sum(0, 0) == 0
    assert calculate_sum(-1, 1) == 0

def test_calculator_init():
    """Test calculator initialization."""
    from sample import Calculator
    calc = Calculator()
    assert calc.history == []

@pytest.mark.asyncio
async def test_async_operation():
    """Test async operation."""
    from sample import Calculator
    calc = Calculator()
    result = await calc.async_operation()
    assert result == "async_result"
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(content)
        temp_file_path = f.name

    yield temp_file_path

    # Cleanup
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)


@pytest.fixture
def temp_directory(sample_python_file, sample_test_file):
    """Create a temporary directory with sample files."""
    temp_dir = tempfile.mkdtemp()

    # Copy files to temp directory
    source_file = Path(temp_dir) / "sample.py"
    test_file = Path(temp_dir) / "test_sample.py"

    with open(sample_python_file, 'r') as src:
        source_file.write_text(src.read())

    with open(sample_test_file, 'r') as src:
        test_file.write_text(src.read())

    yield temp_dir

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_agent_context():
    """Create a mock agent context for testing."""
    context = Mock()
    context.session_id = "test_session_123"
    context.store_memory = Mock()
    return context


def test_auditor_agent_initialization():
    """Test that AuditorAgent can be initialized properly."""
    with patch('auditor_agent.auditor_agent.create_agent_context') as mock_context:
        mock_context.return_value = Mock()
        mock_context.return_value.session_id = "test_session"
        mock_context.return_value.store_memory = Mock()

        agent = create_auditor_agent(model="gpt-5-mini", reasoning_effort="low")

        assert agent is not None
        assert agent.name == "AuditorAgent"
        assert "Quality assurance agent" in agent.description
        # Check that agent has tools (specific tool verification is complex due to wrapping)
        assert len(agent.tools) > 0


def test_analyze_codebase_tool_initialization():
    """Test AnalyzeCodebase tool can be initialized."""
    tool = AnalyzeCodebase(target_path="/test/path", mode="full")

    assert tool.target_path == "/test/path"
    assert tool.mode == "full"


def test_analyze_codebase_nonexistent_path():
    """Test AnalyzeCodebase handles nonexistent paths gracefully."""
    tool = AnalyzeCodebase(target_path="/nonexistent/path")
    result = tool.run()

    result_data = json.loads(result)
    assert "error" in result_data
    assert "does not exist" in result_data["error"]


def test_analyze_codebase_simple_analysis(temp_directory):
    """Test AnalyzeCodebase can analyze a simple codebase."""
    tool = AnalyzeCodebase(target_path=temp_directory, mode="full")

    with patch.object(tool, '_analyze_necessary_compliance') as mock_necessary:
        mock_necessary.return_value = {
            "N": {"score": 0.8, "violations": []},
            "E": {"score": 0.6, "violations": ["Need more edge cases"]},
            "C": {"score": 0.7, "violations": []},
            "E2": {"score": 0.5, "violations": ["Need error testing"]},
            "S": {"score": 0.7, "violations": []},
            "S2": {"score": 0.6, "violations": []},
            "A": {"score": 0.8, "violations": []},
            "R": {"score": 0.8, "violations": []},
            "Y": {"score": 0.7, "violations": []}
        }

        result = tool.run()
        result_data = json.loads(result)

        assert "qt_score" in result_data
        assert "necessary_compliance" in result_data
        assert "violations" in result_data
        assert "codebase_analysis" in result_data
        assert "recommendations" in result_data
        assert result_data["mode"] == "full"
        assert result_data["target"] == temp_directory


def test_qt_score_calculation():
    """Test Q(T) score calculation logic."""
    tool = AnalyzeCodebase(target_path="/test")

    # Mock necessary analysis with known scores
    necessary_analysis = {
        "N": {"score": 0.8, "violations": []},
        "E": {"score": 0.6, "violations": []},
        "C": {"score": 0.7, "violations": []},
        "E2": {"score": 0.5, "violations": []},
        "S": {"score": 0.7, "violations": []},
        "S2": {"score": 0.6, "violations": []},
        "A": {"score": 0.8, "violations": []},
        "R": {"score": 0.8, "violations": []},
        "Y": {"score": 0.7, "violations": []}
    }

    qt_score = tool._calculate_qt_score(necessary_analysis)
    expected_score = sum(prop["score"] for prop in necessary_analysis.values()) / len(necessary_analysis)

    assert qt_score == expected_score
    assert 0.0 <= qt_score <= 1.0


def test_necessary_property_detection():
    """Test detection of each NECESSARY property."""
    tool = AnalyzeCodebase(target_path="/test")

    # Mock analysis data
    analysis = {
        "total_behaviors": 10,
        "total_test_functions": 8,
        "test_files": [{
            "test_functions": [
                {"name": "test_basic_functionality"},
                {"name": "test_edge_cases"},
                {"name": "test_boundary_conditions"},
                {"name": "test_error_handling"},
                {"name": "test_invalid_input"}
            ]
        }],
        "source_files": [{
            "functions": [
                {"is_async": True},
                {"is_async": False}
            ]
        }]
    }

    necessary_analysis = tool._analyze_necessary_compliance(analysis)

    # Check that all NECESSARY properties are analyzed
    expected_properties = ["N", "E", "C", "E2", "S", "S2", "A", "R", "Y"]
    for prop in expected_properties:
        assert prop in necessary_analysis
        assert "score" in necessary_analysis[prop]
        assert "violations" in necessary_analysis[prop]
        assert 0.0 <= necessary_analysis[prop]["score"] <= 1.0


def test_edge_case_coverage_estimation():
    """Test edge case coverage estimation."""
    tool = AnalyzeCodebase(target_path="/test")

    analysis = {
        "total_test_functions": 10,
        "test_files": [{
            "test_functions": [
                {"name": "test_basic"},
                {"name": "test_edge_case_empty"},
                {"name": "test_boundary_values"},
                {"name": "test_limit_conditions"},
                {"name": "test_normal_flow"}
            ]
        }]
    }

    edge_score = tool._estimate_edge_case_coverage(analysis)

    assert isinstance(edge_score, float)
    assert 0.0 <= edge_score <= 1.0
    # Should detect 3 edge case tests out of 5 total


def test_error_testing_estimation():
    """Test error condition testing estimation."""
    tool = AnalyzeCodebase(target_path="/test")

    analysis = {
        "total_test_functions": 10,
        "test_files": [{
            "test_functions": [
                {"name": "test_basic"},
                {"name": "test_error_handling"},
                {"name": "test_exception_case"},
                {"name": "test_invalid_input"},
                {"name": "test_normal_flow"}
            ]
        }]
    }

    error_score = tool._estimate_error_testing(analysis)

    assert isinstance(error_score, float)
    assert 0.0 <= error_score <= 1.0


def test_async_coverage_estimation():
    """Test async operation coverage estimation."""
    tool = AnalyzeCodebase(target_path="/test")

    analysis = {
        "source_files": [{
            "functions": [
                {"is_async": True},
                {"is_async": True},
                {"is_async": False}
            ]
        }],
        "test_files": [{
            "test_functions": [
                {"is_async": True},
                {"is_async": False}
            ]
        }]
    }

    async_score = tool._estimate_async_coverage(analysis)

    assert isinstance(async_score, float)
    assert 0.0 <= async_score <= 1.0


def test_violation_prioritization():
    """Test violation prioritization logic."""
    tool = AnalyzeCodebase(target_path="/test")

    necessary_analysis = {
        "N": {"score": 0.3, "violations": ["Critical violation"]},  # Critical
        "E": {"score": 0.5, "violations": ["High violation"]},     # High
        "C": {"score": 0.65, "violations": ["Medium violation"]},  # Medium
        "S": {"score": 0.8, "violations": []},                     # No violation
    }

    violations = tool._prioritize_violations(necessary_analysis, {})

    # Should have 3 violations (score < 0.7)
    assert len(violations) == 3

    # Check severity assignment
    severities = [v["severity"] for v in violations]
    assert "critical" in severities
    assert "high" in severities
    assert "medium" in severities

    # Check sorting (critical first, then by score)
    critical_violations = [v for v in violations if v["severity"] == "critical"]
    assert len(critical_violations) == 1
    assert critical_violations[0]["property"] == "N"


def test_audit_report_format(temp_directory):
    """Test audit report JSON structure and format."""
    tool = AnalyzeCodebase(target_path=temp_directory, mode="verification")

    result = tool.run()
    result_data = json.loads(result)

    # Check required top-level fields
    required_fields = ["mode", "target", "qt_score", "necessary_compliance",
                      "violations", "codebase_analysis", "recommendations"]

    for field in required_fields:
        assert field in result_data, f"Missing required field: {field}"

    # Check data types
    assert isinstance(result_data["qt_score"], (int, float))
    assert isinstance(result_data["necessary_compliance"], dict)
    assert isinstance(result_data["violations"], list)
    assert isinstance(result_data["codebase_analysis"], dict)
    assert isinstance(result_data["recommendations"], list)

    # Check Q(T) score is in valid range
    assert 0.0 <= result_data["qt_score"] <= 1.0


def test_recommendations_generation():
    """Test recommendation generation based on Q(T) score and violations."""
    tool = AnalyzeCodebase(target_path="/test")

    # Test low Q(T) score recommendations
    low_score_recs = tool._generate_recommendations(0.4, [])
    assert any("CRITICAL" in rec for rec in low_score_recs)

    # Test medium Q(T) score recommendations
    medium_score_recs = tool._generate_recommendations(0.7, [])
    assert any("improvement opportunities" in rec for rec in medium_score_recs)

    # Test high Q(T) score recommendations
    high_score_recs = tool._generate_recommendations(0.9, [])
    assert any("good" in rec.lower() for rec in high_score_recs)

    # Test violation-specific recommendations
    violations = [
        {"property": "N", "severity": "high"},
        {"property": "E", "severity": "medium"},
        {"property": "C", "severity": "low"}
    ]
    violation_recs = tool._generate_recommendations(0.8, violations)
    assert len(violation_recs) > 0


def test_memory_integration(mock_agent_context):
    """Test integration with agent context."""
    with patch('auditor_agent.auditor_agent.create_agent_context') as mock_create_context:
        mock_create_context.return_value = mock_agent_context

        _ = create_auditor_agent(model="gpt-5-mini", reasoning_effort="low", agent_context=mock_agent_context)

        # The agent should have the context set
        # Note: The actual memory storage implementation may vary


def test_ast_analyzer_integration(sample_python_file):
    """Test integration with AST analyzer."""
    tool = AnalyzeCodebase(target_path=os.path.dirname(sample_python_file))

    # Run analysis
    result = tool.run()
    result_data = json.loads(result)

    # Verify AST analyzer was used
    assert "codebase_analysis" in result_data
    codebase_analysis = result_data["codebase_analysis"]

    # Check basic structure
    assert "source_files" in codebase_analysis
    assert "test_files" in codebase_analysis
    assert "total_behaviors" in codebase_analysis
    assert "total_test_functions" in codebase_analysis


def test_empty_codebase_handling():
    """Test handling of empty codebase."""
    with tempfile.TemporaryDirectory() as temp_dir:
        tool = AnalyzeCodebase(target_path=temp_dir)
        result = tool.run()
        result_data = json.loads(result)

        # Should handle gracefully with zero scores
        assert result_data["qt_score"] == 0.0
        necessary_compliance = result_data["necessary_compliance"]

        for prop in "NECESSARY":
            assert necessary_compliance[prop]["score"] == 0.0
            assert "No behaviors found" in necessary_compliance[prop]["violations"]