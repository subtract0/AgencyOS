"""
Tests for Feature Pipeline (Phase 4).

Tests the end-to-end feature generation including:
- Intent parsing
- Codebase analysis
- Spec generation
- Code generation
- Validation
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))


class TestFeatureIntent:
    """Tests for FeatureIntent dataclass."""

    def test_feature_intent_creation(self):
        """Test creating a feature intent."""
        from tools.feature_pipeline import FeatureIntent

        intent = FeatureIntent(
            name="User Authentication",
            description="Add user authentication to the app",
            requirements=["Must support OAuth", "Should handle sessions"],
            constraints=["Must not store passwords in plain text"],
            acceptance_criteria=["Users can log in", "Users can log out"],
            priority="high",
        )

        assert intent.name == "User Authentication"
        assert intent.priority == "high"
        assert len(intent.requirements) == 2

    def test_feature_intent_defaults(self):
        """Test feature intent default values."""
        from tools.feature_pipeline import FeatureIntent

        intent = FeatureIntent(
            name="Simple Feature",
            description="A simple feature",
            requirements=[],
            constraints=[],
            acceptance_criteria=[],
        )

        assert intent.priority == "medium"
        assert intent.related_files == []


class TestFeatureSpec:
    """Tests for FeatureSpec dataclass."""

    def test_feature_spec_creation(self):
        """Test creating a feature spec."""
        from tools.feature_pipeline import FeatureIntent, FeatureSpec

        intent = FeatureIntent(
            name="Test",
            description="Test feature",
            requirements=[],
            constraints=[],
            acceptance_criteria=[],
        )

        spec = FeatureSpec(
            intent=intent,
            target_module="test_module",
            target_file="tools/test_module.py",
            functions=[{"name": "process", "return_type": "dict"}],
            classes=[],
            tests=[{"name": "test_process", "target": "process"}],
            integration_points=[],
            dependencies=["json"],
        )

        assert spec.target_module == "test_module"
        assert len(spec.functions) == 1


class TestGenerationResult:
    """Tests for GenerationResult dataclass."""

    def test_generation_result_creation(self):
        """Test creating a generation result."""
        from tools.feature_pipeline import FeatureIntent, FeatureSpec, GenerationResult

        intent = FeatureIntent(
            name="Gen",
            description="",
            requirements=[],
            constraints=[],
            acceptance_criteria=[],
        )

        spec = FeatureSpec(
            intent=intent,
            target_module="gen",
            target_file="gen.py",
            functions=[],
            classes=[],
            tests=[],
            integration_points=[],
            dependencies=[],
        )

        result = GenerationResult(
            spec=spec,
            code_files={"gen.py": "# Generated code"},
            test_files={"test_gen.py": "# Generated tests"},
            integration_changes=[],
            validation_passed=True,
            errors=[],
        )

        assert result.validation_passed
        assert len(result.code_files) == 1


class TestIntentParser:
    """Tests for IntentParser class."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        from tools.feature_pipeline import IntentParser

        return IntentParser()

    def test_parse_simple_request(self, parser):
        """Test parsing a simple feature request."""
        request = "Add a user authentication system to the application."

        result = parser.parse(request)

        assert result.is_ok()
        intent = result.unwrap()
        assert "authentication" in intent.name.lower() or "user" in intent.name.lower()

    def test_parse_with_requirements(self, parser):
        """Test parsing request with requirements."""
        request = """
        Create a data export feature.

        The feature must support CSV format.
        It should handle large datasets.
        It needs to validate input data.
        """

        result = parser.parse(request)

        assert result.is_ok()
        intent = result.unwrap()
        assert len(intent.requirements) >= 1

    def test_parse_with_constraints(self, parser):
        """Test parsing request with constraints."""
        request = """
        Build a file uploader.

        Must not accept files larger than 10MB.
        Should not allow executable files.
        Cannot store files without encryption.
        """

        result = parser.parse(request)

        assert result.is_ok()
        intent = result.unwrap()
        assert len(intent.constraints) >= 1

    def test_parse_with_list_criteria(self, parser):
        """Test parsing request with listed criteria."""
        request = """
        Implement a search feature with the following requirements:

        1. Support full-text search
        2. Return results within 100ms
        - Handle typos
        - Provide suggestions
        """

        result = parser.parse(request)

        assert result.is_ok()
        intent = result.unwrap()
        assert len(intent.acceptance_criteria) >= 1

    def test_parse_infers_priority(self, parser):
        """Test that parser infers priority from language."""
        urgent = "URGENT: Fix the critical authentication bug immediately!"
        result = parser.parse(urgent)

        assert result.is_ok()
        intent = result.unwrap()
        assert intent.priority in ("critical", "high")

    def test_parse_rejects_short_request(self, parser):
        """Test that short requests are rejected."""
        result = parser.parse("add")

        assert result.is_err()
        assert "too short" in result.unwrap_err()

    def test_parse_empty_request(self, parser):
        """Test that empty requests are rejected."""
        result = parser.parse("")

        assert result.is_err()


class TestFeaturePipeline:
    """Tests for FeaturePipeline class."""

    @pytest.fixture
    def pipeline(self, tmp_path):
        """Create pipeline instance."""
        from tools.feature_pipeline import FeaturePipeline

        # Create minimal project structure
        (tmp_path / "tools").mkdir()
        (tmp_path / "tools" / "__init__.py").write_text("")

        return FeaturePipeline(tmp_path)

    def test_generate_feature_dry_run(self, pipeline):
        """Test feature generation in dry run mode."""
        request = "Create a utility function for formatting dates in ISO format."

        result = pipeline.generate_feature(request, dry_run=True)

        assert result.is_ok()
        report = result.unwrap()
        assert report.feature_name is not None
        assert "intent_parsing" in report.stages_completed

    def test_generate_feature_writes_files(self, pipeline, tmp_path):
        """Test that feature generation writes files."""
        request = "Add a simple data validator that checks if input is valid JSON."

        result = pipeline.generate_feature(request, dry_run=False)

        assert result.is_ok()
        report = result.unwrap()
        assert report.generation_result is not None

    def test_pipeline_stages_complete(self, pipeline):
        """Test that all stages complete."""
        request = "Build a configuration loader that reads from environment variables."

        result = pipeline.generate_feature(request, dry_run=True)

        assert result.is_ok()
        report = result.unwrap()

        expected_stages = ["intent_parsing", "codebase_analysis", "spec_generation", "code_generation", "validation"]
        for stage in expected_stages:
            assert stage in report.stages_completed

    def test_get_status_not_running(self, pipeline):
        """Test status when not running."""
        status = pipeline.get_status()

        assert status["running"] is False

    def test_get_status_after_run(self, pipeline):
        """Test status after running."""
        pipeline.generate_feature("Add a helper function.", dry_run=True)

        status = pipeline.get_status()

        assert status["running"] is False
        assert status["feature_name"] is not None

    def test_validation_catches_syntax_errors(self, pipeline):
        """Test that validation catches syntax errors."""
        from tools.feature_pipeline import GenerationResult, FeatureIntent, FeatureSpec

        intent = FeatureIntent(
            name="Bad",
            description="",
            requirements=[],
            constraints=[],
            acceptance_criteria=[],
        )

        spec = FeatureSpec(
            intent=intent,
            target_module="bad",
            target_file="bad.py",
            functions=[],
            classes=[],
            tests=[],
            integration_points=[],
            dependencies=[],
        )

        generated = GenerationResult(
            spec=spec,
            code_files={"bad.py": "def broken(:\n    pass"},  # Syntax error
            test_files={},
            integration_changes=[],
            validation_passed=False,
            errors=[],
        )

        result = pipeline._validate(generated)

        assert result.is_err()
        assert "Syntax error" in result.unwrap_err()

    def test_suggest_location_for_tool(self, pipeline):
        """Test location suggestion for tool."""
        from tools.feature_pipeline import FeatureIntent

        intent = FeatureIntent(
            name="new tool for processing",
            description="A tool for data processing",
            requirements=[],
            constraints=[],
            acceptance_criteria=[],
        )

        location = pipeline._suggest_location(intent)

        assert location == "tools/"

    def test_suggest_location_for_agent(self, pipeline):
        """Test location suggestion for agent."""
        from tools.feature_pipeline import FeatureIntent

        intent = FeatureIntent(
            name="new agent for automation",
            description="An agent that automates tasks",
            requirements=[],
            constraints=[],
            acceptance_criteria=[],
        )

        location = pipeline._suggest_location(intent)

        assert location == "agents/"


class TestPipelineReport:
    """Tests for PipelineReport dataclass."""

    def test_pipeline_report_creation(self):
        """Test creating a pipeline report."""
        from datetime import datetime

        from tools.feature_pipeline import PipelineReport

        report = PipelineReport(
            feature_name="Test Feature",
            started_at=datetime.now(),
            completed_at=None,
            stages_completed=["intent_parsing"],
            current_stage="codebase_analysis",
            generation_result=None,
            success=False,
            error=None,
        )

        assert report.feature_name == "Test Feature"
        assert report.current_stage == "codebase_analysis"
        assert len(report.stages_completed) == 1


class TestIntegration:
    """Integration tests for the pipeline."""

    @pytest.fixture
    def pipeline(self, tmp_path):
        """Create pipeline with test structure."""
        from tools.feature_pipeline import FeaturePipeline

        # Create test project
        (tmp_path / "tools").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "unit").mkdir()
        (tmp_path / "tests" / "unit" / "tools").mkdir()

        return FeaturePipeline(tmp_path)

    def test_end_to_end_dry_run(self, pipeline):
        """Test complete pipeline execution."""
        request = """
        Add a rate limiter utility that:
        - Limits requests to 100 per minute
        - Should track per-user limits
        - Must not block legitimate traffic

        Requirements:
        1. Thread-safe implementation
        2. Configurable limits
        """

        result = pipeline.generate_feature(request, dry_run=True)

        assert result.is_ok()
        report = result.unwrap()
        assert report.success or len(report.stages_completed) >= 4
        assert report.generation_result is not None
        assert len(report.generation_result.code_files) >= 1

    def test_generated_code_is_valid_python(self, pipeline):
        """Test that generated code is valid Python."""
        import ast

        result = pipeline.generate_feature(
            "Create a helper function for string formatting.",
            dry_run=True,
        )

        assert result.is_ok()
        report = result.unwrap()

        if report.generation_result:
            for path, code in report.generation_result.code_files.items():
                # Should parse without error
                ast.parse(code)

    def test_generated_tests_are_valid(self, pipeline):
        """Test that generated tests are valid Python."""
        import ast

        result = pipeline.generate_feature(
            "Build a validator for email addresses.",
            dry_run=True,
        )

        assert result.is_ok()
        report = result.unwrap()

        if report.generation_result:
            for path, code in report.generation_result.test_files.items():
                # Should parse without error
                ast.parse(code)
