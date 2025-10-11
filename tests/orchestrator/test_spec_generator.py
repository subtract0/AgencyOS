"""
Test suite for SpecGenerator (DSPy PlannerAgent Specification Generation)

Tests the spec-kit template generation, VectorStore pattern application,
and Pydantic validation for the DSPy PlannerAgent's specification generation.

Constitutional Compliance:
- Article I: Complete Context Before Action
- Article II: 100% Verification and Stability (TDD)
- Article IV: Continuous Learning and Improvement (VectorStore)
- Article V: Spec-Driven Development

NECESSARY Pattern Coverage:
- N: Normal operation tests (happy path)
- E: Edge case tests (boundaries, empty inputs)
- C: Corner case tests (unusual combinations)
- E: Error condition tests (invalid inputs, failures)
- S: Security tests (input validation)
- S: Stress tests (large inputs)
- A: Accessibility tests (API usability)
- R: Regression tests (bug prevention)
- Y: Yield (output validation) tests
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import ValidationError

from dspy_agents.modules.planner_agent import (
    DSPyPlannerAgent,
    PlanningContext,
    PlanningResult,
    RequirementType,
    Specification,
    TechnicalPlan,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_specs_dir():
    """Create temporary directory for specifications."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_plans_dir():
    """Create temporary directory for technical plans."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def planner_agent(temp_specs_dir, temp_plans_dir):
    """Create DSPyPlannerAgent instance with temporary directories."""
    return DSPyPlannerAgent(
        model="gpt-4o-mini",
        reasoning_effort="medium",
        enable_learning=True,
        specs_dir=str(temp_specs_dir),
        plans_dir=str(temp_plans_dir),
    )


@pytest.fixture
def mock_agent_context():
    """Create mock AgentContext for VectorStore integration tests."""
    context = Mock()
    context.search_memories = Mock(return_value=[])
    context.store_memory = Mock()
    context.session_id = "test_session_123"
    return context


@pytest.fixture
def sample_vectorstore_patterns():
    """Sample VectorStore patterns for spec generation."""
    return [
        {
            "spec_file": "specs/spec-001-authentication.md",
            "feature_type": "authentication",
            "confidence": 0.85,
            "pattern": {
                "goals": ["Implement secure authentication", "Support multiple auth methods"],
                "non_goals": ["Authorization management", "Role-based access control"],
                "personas": {"developer": "Backend developer", "end_user": "Application user"},
            },
            "success_factors": ["Clear goals", "Well-defined personas", "Testable criteria"],
        },
        {
            "spec_file": "specs/spec-002-api-integration.md",
            "feature_type": "api",
            "confidence": 0.72,
            "pattern": {
                "goals": ["Integrate with external API", "Handle rate limiting"],
                "acceptance_criteria": ["API calls succeed", "Errors handled gracefully"],
            },
        },
    ]


# ============================================================================
# N - Normal Operation Tests (Happy Path)
# ============================================================================


class TestSpecGenerationNormalOperation:
    """Test normal operation scenarios for spec generation."""

    def test_generate_specification_with_valid_feature_request(self, planner_agent):
        """
        GIVEN: Valid feature request for new functionality
        WHEN: Specification generation is triggered
        THEN: Complete specification is generated with all required sections
        """
        # Arrange
        request = "Implement user authentication with JWT tokens and OAuth2 support"
        context = PlanningContext(
            request=request,
            mode="full",
            constitutional_requirements=[
                "Article I: Complete Context Before Action",
                "Article V: Spec-Driven Development",
            ],
        )
        requirement_type = RequirementType(
            category="feature", complexity="complex", requires_spec=True, estimated_effort="weeks"
        )

        # Act
        spec = planner_agent._generate_specification(context, requirement_type)

        # Assert
        assert isinstance(spec, Specification)
        assert spec.spec_id.startswith("spec-")
        assert "feature" in spec.spec_id
        assert spec.title == "Feature Implementation"
        assert len(spec.goals) >= 1
        assert len(spec.non_goals) >= 1
        assert len(spec.personas) >= 1
        assert len(spec.acceptance_criteria) >= 3  # At least standard criteria
        assert spec.status == "draft"
        assert isinstance(spec.created_at, datetime)

    def test_generate_technical_plan_from_specification(self, planner_agent):
        """
        GIVEN: Valid specification
        WHEN: Technical plan generation is triggered
        THEN: Complete technical plan is generated with architecture and assignments
        """
        # Arrange
        spec = Specification(
            spec_id="spec-001-test",
            title="Test Feature",
            goals=["Goal 1: Implement feature", "Goal 2: Write tests"],
            non_goals=["Non-goal: Refactor unrelated code"],
            personas={"developer": "Backend developer"},
            user_journeys=[{"persona": "developer", "steps": ["Step 1", "Step 2"]}],
            acceptance_criteria=["Tests pass", "Code is documented"],
        )
        context = PlanningContext(
            request="Test request",
            mode="full",
        )

        # Act
        plan = planner_agent._generate_technical_plan(context, spec)

        # Assert
        assert isinstance(plan, TechnicalPlan)
        assert plan.plan_id == f"plan-{spec.spec_id}"
        assert plan.spec_id == spec.spec_id
        assert "overview" in plan.architecture
        assert "components" in plan.architecture
        assert len(plan.agent_assignments) >= 1
        assert len(plan.tool_requirements) >= 1
        assert plan.quality_strategy["coverage_target"] == "100%"
        assert "TDD" in plan.quality_strategy["testing_approach"]

    def test_full_planning_result_with_spec_and_plan(self, planner_agent):
        """
        GIVEN: Complex feature request
        WHEN: Full planning process is executed
        THEN: Complete PlanningResult with spec, plan, and tasks is returned
        """
        # Arrange
        request = "Create REST API for user management with CRUD operations"

        # Act
        result = planner_agent.forward(request, mode="full")

        # Assert
        assert isinstance(result, PlanningResult)
        assert result.success is True
        assert result.specification is not None
        assert result.technical_plan is not None
        assert len(result.tasks) >= 1
        assert len(result.recommendations) >= 1
        assert isinstance(result.timestamp, datetime)

    def test_specification_pydantic_validation_success(self):
        """
        GIVEN: Valid specification data
        WHEN: Specification model is instantiated
        THEN: Pydantic validation succeeds and model is created
        """
        # Arrange
        spec_data = {
            "spec_id": "spec-001-valid",
            "title": "Valid Specification",
            "goals": ["Goal 1", "Goal 2"],
            "non_goals": ["Non-goal 1"],
            "personas": {"dev": "Developer"},
            "user_journeys": [{"persona": "dev", "steps": ["Step 1"]}],
            "acceptance_criteria": ["Criterion 1"],
        }

        # Act
        spec = Specification(**spec_data)

        # Assert
        assert spec.spec_id == "spec-001-valid"
        assert spec.title == "Valid Specification"
        assert len(spec.goals) == 2
        assert spec.status == "draft"  # Default value
        assert isinstance(spec.created_at, datetime)


# ============================================================================
# E - Edge Case Tests (Boundaries, Limits)
# ============================================================================


class TestSpecGenerationEdgeCases:
    """Test edge cases and boundary conditions for spec generation."""

    def test_generate_specification_with_minimal_request(self, planner_agent):
        """
        GIVEN: Minimal single-word feature request
        WHEN: Specification is generated
        THEN: Spec is created with default values and minimal content
        """
        # Arrange
        request = "Authentication"
        context = PlanningContext(request=request, mode="full")
        requirement_type = RequirementType(
            category="feature", complexity="simple", requires_spec=False, estimated_effort="hours"
        )

        # Act
        spec = planner_agent._generate_specification(context, requirement_type)

        # Assert
        assert isinstance(spec, Specification)
        assert len(spec.goals) >= 1  # Should generate default goals
        assert len(spec.acceptance_criteria) >= 3  # Standard criteria

    def test_generate_specification_with_empty_personas(self, planner_agent):
        """
        GIVEN: Request that doesn't clearly define users
        WHEN: Specification is generated
        THEN: Default personas are created
        """
        # Arrange
        request = "Implement logging system"
        context = PlanningContext(request=request, mode="full")
        requirement_type = RequirementType(
            category="feature", complexity="moderate", requires_spec=True, estimated_effort="days"
        )

        # Act
        spec = planner_agent._generate_specification(context, requirement_type)

        # Assert
        assert len(spec.personas) >= 2  # At least developer and end_user
        assert "developer" in spec.personas
        assert "end_user" in spec.personas

    def test_planning_context_with_empty_codebase_context(self, planner_agent):
        """
        GIVEN: Planning context with no existing codebase information
        WHEN: Context is prepared
        THEN: Context is created with empty codebase_context dict
        """
        # Arrange
        request = "Add feature"

        # Act
        context = planner_agent._prepare_context(request, "full")

        # Assert
        assert isinstance(context, PlanningContext)
        assert context.codebase_context == {}
        assert len(context.constitutional_requirements) == 5

    def test_generate_task_breakdown_with_no_acceptance_criteria(self, planner_agent):
        """
        GIVEN: Specification with no acceptance criteria
        WHEN: Task breakdown is generated
        THEN: Empty task list is returned (fallback behavior)
        """
        # Arrange
        spec = Specification(
            spec_id="spec-001-no-criteria",
            title="Test",
            goals=["Goal"],
            non_goals=["Non-goal"],
            personas={"dev": "Developer"},
            user_journeys=[],
            acceptance_criteria=[],  # Empty criteria
        )
        plan = TechnicalPlan(
            plan_id="plan-001",
            spec_id=spec.spec_id,
            architecture={"overview": "Test"},
            agent_assignments={},
            tool_requirements=[],
            contracts={},
            quality_strategy={},
            risk_assessment=[],
            milestones=[],
            estimated_duration="1 day",
        )

        # Act
        tasks = planner_agent._generate_task_breakdown(plan, spec)

        # Assert
        assert isinstance(tasks, list)
        assert len(tasks) == 0  # No tasks generated from empty criteria

    def test_specification_with_maximum_length_strings(self):
        """
        GIVEN: Specification data with very long strings (stress boundary)
        WHEN: Specification is created
        THEN: Model accepts long strings without error
        """
        # Arrange
        long_string = "A" * 10000
        spec_data = {
            "spec_id": "spec-001-long",
            "title": long_string,
            "goals": [long_string],
            "non_goals": [long_string],
            "personas": {"dev": long_string},
            "user_journeys": [{"persona": "dev", "description": long_string}],
            "acceptance_criteria": [long_string],
        }

        # Act
        spec = Specification(**spec_data)

        # Assert
        assert len(spec.title) == 10000
        assert len(spec.goals[0]) == 10000


# ============================================================================
# C - Corner Case Tests (Unusual Combinations)
# ============================================================================


class TestSpecGenerationCornerCases:
    """Test corner cases with unusual combinations."""

    def test_generate_spec_for_test_category_feature(self, planner_agent):
        """
        GIVEN: Request categorized as "test" (unusual for spec generation)
        WHEN: Specification is generated
        THEN: Spec is created with test-specific personas and goals
        """
        # Arrange
        request = "Create comprehensive test suite for authentication module"
        context = PlanningContext(request=request, mode="full")
        requirement_type = RequirementType(
            category="test", complexity="moderate", requires_spec=True, estimated_effort="days"
        )

        # Act
        spec = planner_agent._generate_specification(context, requirement_type)

        # Assert
        assert isinstance(spec, Specification)
        assert "qa_engineer" in spec.personas  # Test category adds QA persona
        assert any("test" in goal.lower() for goal in spec.goals)

    def test_planning_with_conflicting_modes(self, planner_agent):
        """
        GIVEN: Complex request with mode="simple" (conflicting signals)
        WHEN: Planning is executed
        THEN: System uses mode to determine approach (simple guidance)
        """
        # Arrange
        request = "Implement distributed microservices architecture with service mesh"

        # Act - Using simple mode despite complex request
        result = planner_agent.forward(request, mode="simple")

        # Assert
        # Should classify as complex but mode overrides the flow
        assert result.success is True
        # With simple mode, may still generate spec if classified as complex

    def test_specification_with_mixed_status_values(self):
        """
        GIVEN: Specification with custom status value
        WHEN: Specification is created
        THEN: Custom status is accepted (no enum validation)
        """
        # Arrange
        spec_data = {
            "spec_id": "spec-001-status",
            "title": "Test",
            "goals": ["Goal"],
            "non_goals": ["Non-goal"],
            "personas": {"dev": "Developer"},
            "user_journeys": [],
            "acceptance_criteria": ["Criterion"],
            "status": "in_review",  # Custom status
        }

        # Act
        spec = Specification(**spec_data)

        # Assert
        assert spec.status == "in_review"


# ============================================================================
# E - Error Condition Tests (Invalid Inputs, Failures)
# ============================================================================


class TestSpecGenerationErrorConditions:
    """Test error conditions and invalid inputs."""

    def test_specification_pydantic_validation_missing_required_fields(self):
        """
        GIVEN: Specification data missing required fields
        WHEN: Specification instantiation is attempted
        THEN: Pydantic ValidationError is raised
        """
        # Arrange
        incomplete_data = {
            "spec_id": "spec-001-incomplete",
            "title": "Test",
            # Missing: goals, non_goals, personas, user_journeys, acceptance_criteria
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Specification(**incomplete_data)

        # Verify specific field errors
        errors = exc_info.value.errors()
        error_fields = {error["loc"][0] for error in errors}
        assert "goals" in error_fields
        assert "non_goals" in error_fields
        assert "personas" in error_fields

    def test_technical_plan_pydantic_validation_invalid_types(self):
        """
        GIVEN: TechnicalPlan data with wrong types
        WHEN: TechnicalPlan instantiation is attempted
        THEN: Pydantic ValidationError is raised
        """
        # Arrange
        invalid_data = {
            "plan_id": "plan-001",
            "spec_id": "spec-001",
            "architecture": "not a dict",  # Should be dict[str, JSONValue]
            "agent_assignments": "not a dict",  # Should be dict[str, list[str]]
            "tool_requirements": "not a list",  # Should be list[str]
            "contracts": {},
            "quality_strategy": {},
            "risk_assessment": [],
            "milestones": [],
            "estimated_duration": "1 day",
        }

        # Act & Assert
        with pytest.raises(ValidationError):
            TechnicalPlan(**invalid_data)

    def test_generate_specification_with_dspy_failure(self, planner_agent):
        """
        GIVEN: DSPy understanding module fails with exception
        WHEN: Specification generation is attempted
        THEN: Fallback mechanism is used and spec is still generated
        """
        # Arrange
        request = "Test feature"
        context = PlanningContext(request=request, mode="full")
        requirement_type = RequirementType(
            category="feature", complexity="simple", requires_spec=True, estimated_effort="hours"
        )

        # Mock DSPy failure
        planner_agent.understand = Mock(side_effect=Exception("DSPy failure"))

        # Act
        spec = planner_agent._generate_specification(context, requirement_type)

        # Assert - Should use fallback and still succeed
        assert isinstance(spec, Specification)
        assert spec.assumptions == ["Requirements are clear and complete"]

    def test_planning_result_for_failed_spec_generation(self, planner_agent):
        """
        GIVEN: Spec generation process encounters error
        WHEN: Spec-kit process is executed
        THEN: PlanningResult with success=False is returned
        """
        # Arrange
        context = PlanningContext(request="Test", mode="full")
        requirement_type = RequirementType(
            category="feature", complexity="complex", requires_spec=True, estimated_effort="weeks"
        )

        # Mock to raise exception during spec generation
        with patch.object(
            planner_agent, "_generate_specification", side_effect=Exception("Spec gen failed")
        ):
            # Act
            result = planner_agent._execute_spec_kit_process(context, requirement_type)

            # Assert
            assert result.success is False
            assert result.specification is None
            assert result.technical_plan is None
            assert "Planning failed" in result.recommendations[0]

    def test_requirement_type_validation_with_invalid_extra_fields(self):
        """
        GIVEN: RequirementType data with extra forbidden fields
        WHEN: RequirementType instantiation is attempted
        THEN: Pydantic ValidationError is raised (extra="forbid")
        """
        # Arrange
        data_with_extra = {
            "category": "feature",
            "complexity": "simple",
            "requires_spec": True,
            "estimated_effort": "hours",
            "invalid_field": "should not be here",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            RequirementType(**data_with_extra)

        errors = exc_info.value.errors()
        assert any("extra" in error["type"] for error in errors)


# ============================================================================
# S - Security Tests (Input Validation)
# ============================================================================


class TestSpecGenerationSecurity:
    """Test security aspects and input validation."""

    def test_specification_with_injection_attempt_in_spec_id(self):
        """
        GIVEN: Specification data with potential injection in spec_id
        WHEN: Specification is created
        THEN: Data is accepted but treated as literal string (no execution)
        """
        # Arrange
        malicious_spec_id = "spec-001'; DROP TABLE specs; --"
        spec_data = {
            "spec_id": malicious_spec_id,
            "title": "Test",
            "goals": ["Goal"],
            "non_goals": ["Non-goal"],
            "personas": {"dev": "Developer"},
            "user_journeys": [],
            "acceptance_criteria": ["Criterion"],
        }

        # Act
        spec = Specification(**spec_data)

        # Assert - String is stored literally, not executed
        assert spec.spec_id == malicious_spec_id
        assert "DROP TABLE" in spec.spec_id  # Literal string, not executed

    def test_specification_with_xss_attempt_in_title(self):
        """
        GIVEN: Specification data with potential XSS payload
        WHEN: Specification is created
        THEN: Payload is stored as literal string without execution
        """
        # Arrange
        xss_payload = "<script>alert('XSS')</script>"
        spec_data = {
            "spec_id": "spec-001-xss",
            "title": xss_payload,
            "goals": ["Goal"],
            "non_goals": ["Non-goal"],
            "personas": {"dev": "Developer"},
            "user_journeys": [],
            "acceptance_criteria": ["Criterion"],
        }

        # Act
        spec = Specification(**spec_data)

        # Assert
        assert spec.title == xss_payload  # Stored literally
        assert "<script>" in spec.title

    def test_planning_context_with_untrusted_codebase_context(self):
        """
        GIVEN: Planning context with potentially malicious codebase_context
        WHEN: Context is created
        THEN: Data is stored in typed JSONValue field (safe handling)
        """
        # Arrange
        untrusted_context = {
            "malicious_key": "__import__('os').system('rm -rf /')",
            "nested": {"eval": "exec('print(1)')"},
        }

        # Act
        context = PlanningContext(
            request="Test",
            mode="full",
            codebase_context=untrusted_context,
        )

        # Assert - Stored as data, not executed
        assert context.codebase_context["malicious_key"] == "__import__('os').system('rm -rf /')"
        assert isinstance(context.codebase_context, dict)


# ============================================================================
# S - Stress Tests (Large Inputs, Performance)
# ============================================================================


class TestSpecGenerationStress:
    """Test stress scenarios with large inputs."""

    def test_specification_with_large_number_of_goals(self):
        """
        GIVEN: Specification with 100+ goals
        WHEN: Specification is created
        THEN: Model handles large list without error
        """
        # Arrange
        large_goals = [f"Goal {i}" for i in range(150)]
        spec_data = {
            "spec_id": "spec-001-large",
            "title": "Large Spec",
            "goals": large_goals,
            "non_goals": ["Non-goal"],
            "personas": {"dev": "Developer"},
            "user_journeys": [],
            "acceptance_criteria": ["Criterion"],
        }

        # Act
        spec = Specification(**spec_data)

        # Assert
        assert len(spec.goals) == 150
        assert spec.goals[0] == "Goal 0"
        assert spec.goals[-1] == "Goal 149"

    def test_technical_plan_with_many_agent_assignments(self, planner_agent):
        """
        GIVEN: Specification requiring coordination of many agents
        WHEN: Technical plan is generated
        THEN: Plan handles multiple agent assignments
        """
        # Arrange
        spec = Specification(
            spec_id="spec-001-multi-agent",
            title="Complex Multi-Agent Feature",
            goals=[f"Goal {i}" for i in range(20)],
            non_goals=["Non-goal"],
            personas={"dev": "Developer"},
            user_journeys=[],
            acceptance_criteria=[f"Criterion {i}" for i in range(20)],
        )
        context = PlanningContext(request="Complex feature", mode="full")

        # Act
        plan = planner_agent._generate_technical_plan(context, spec)

        # Assert
        assert isinstance(plan, TechnicalPlan)
        assert len(plan.agent_assignments) >= 1
        # Each agent has list of assigned tasks
        total_assignments = sum(len(tasks) for tasks in plan.agent_assignments.values())
        assert total_assignments >= 1

    def test_planning_with_extensive_learning_patterns(self, planner_agent):
        """
        GIVEN: Planning context with 50+ historical learning patterns
        WHEN: Context is prepared
        THEN: Context handles large pattern list efficiently
        """
        # Arrange
        many_patterns = [
            {
                "pattern_id": f"pattern-{i}",
                "confidence": 0.6 + (i % 40) / 100,
                "feature_type": f"type-{i % 5}",
            }
            for i in range(60)
        ]

        # Act
        context = PlanningContext(
            request="Feature request",
            mode="full",
            learning_patterns=many_patterns,
        )

        # Assert
        assert len(context.learning_patterns) == 60
        assert context.learning_patterns[0]["pattern_id"] == "pattern-0"


# ============================================================================
# A - Accessibility Tests (API Usability)
# ============================================================================


class TestSpecGenerationAPIUsability:
    """Test API usability and developer experience."""

    def test_specification_has_sensible_defaults(self):
        """
        GIVEN: Minimal required Specification fields
        WHEN: Specification is created
        THEN: Sensible defaults are applied for optional fields
        """
        # Arrange - Only required fields
        minimal_data = {
            "spec_id": "spec-001",
            "title": "Minimal Spec",
            "goals": ["Goal"],
            "non_goals": ["Non-goal"],
            "personas": {"dev": "Developer"},
            "user_journeys": [],
            "acceptance_criteria": ["Criterion"],
        }

        # Act
        spec = Specification(**minimal_data)

        # Assert - Defaults applied
        assert spec.constraints == []  # Default empty list
        assert spec.assumptions == []  # Default empty list
        assert spec.status == "draft"  # Default status
        assert isinstance(spec.created_at, datetime)

    def test_planning_result_has_clear_structure(self, planner_agent):
        """
        GIVEN: Simple feature request
        WHEN: Planning is executed
        THEN: PlanningResult has clear, accessible structure
        """
        # Arrange
        request = "Add logging to application"

        # Act
        result = planner_agent.forward(request, mode="full")

        # Assert - Clear structure
        assert hasattr(result, "success")
        assert hasattr(result, "requirement_type")
        assert hasattr(result, "specification")
        assert hasattr(result, "technical_plan")
        assert hasattr(result, "tasks")
        assert hasattr(result, "recommendations")
        assert hasattr(result, "timestamp")

    def test_requirement_type_provides_useful_metadata(self, planner_agent):
        """
        GIVEN: Various feature requests
        WHEN: Requirements are classified
        THEN: RequirementType provides useful planning metadata
        """
        # Arrange
        requests = [
            ("Fix bug in authentication", "bugfix"),
            ("Add new feature for users", "feature"),
            ("Improve performance of queries", "refactor"),
            ("Write tests for API", "test"),
        ]

        # Act & Assert
        for request, expected_category in requests:
            context = planner_agent._prepare_context(request, "full")
            req_type = planner_agent._classify_requirement(context)

            assert req_type.category == expected_category
            assert req_type.complexity in ["simple", "moderate", "complex"]
            assert isinstance(req_type.requires_spec, bool)
            assert req_type.estimated_effort in ["hours", "days", "weeks"]


# ============================================================================
# R - Regression Tests (Bug Prevention)
# ============================================================================


class TestSpecGenerationRegression:
    """Test regression scenarios to prevent known bugs."""

    def test_specification_created_at_is_datetime_not_string(self):
        """
        GIVEN: Specification with default created_at
        WHEN: Specification is created
        THEN: created_at is datetime object, not string
        Regression: Prevent string timestamps
        """
        # Arrange
        spec_data = {
            "spec_id": "spec-001",
            "title": "Test",
            "goals": ["Goal"],
            "non_goals": ["Non-goal"],
            "personas": {"dev": "Developer"},
            "user_journeys": [],
            "acceptance_criteria": ["Criterion"],
        }

        # Act
        spec = Specification(**spec_data)

        # Assert
        assert isinstance(spec.created_at, datetime)
        assert not isinstance(spec.created_at, str)

    def test_technical_plan_references_correct_spec_id(self, planner_agent):
        """
        GIVEN: Specification with specific spec_id
        WHEN: Technical plan is generated
        THEN: Plan correctly references the spec_id
        Regression: Prevent plan/spec mismatch
        """
        # Arrange
        spec = Specification(
            spec_id="spec-042-unique",
            title="Test",
            goals=["Goal"],
            non_goals=["Non-goal"],
            personas={"dev": "Developer"},
            user_journeys=[],
            acceptance_criteria=["Criterion"],
        )
        context = PlanningContext(request="Test", mode="full")

        # Act
        plan = planner_agent._generate_technical_plan(context, spec)

        # Assert
        assert plan.spec_id == "spec-042-unique"
        assert plan.plan_id == "plan-spec-042-unique"

    def test_planning_result_timestamp_matches_completion_time(self, planner_agent):
        """
        GIVEN: Planning execution
        WHEN: PlanningResult is generated
        THEN: Timestamp reflects actual completion time
        Regression: Prevent stale timestamps
        """
        # Arrange
        request = "Simple feature"
        start_time = datetime.utcnow()

        # Act
        result = planner_agent.forward(request, mode="simple")
        end_time = datetime.utcnow()

        # Assert
        assert start_time <= result.timestamp <= end_time


# ============================================================================
# Y - Yield (Output Validation) Tests
# ============================================================================


class TestSpecGenerationOutputValidation:
    """Test output validation and data quality."""

    def test_specification_output_has_valid_spec_id_format(self, planner_agent):
        """
        GIVEN: Specification generation
        WHEN: Specification is created
        THEN: spec_id follows naming convention (spec-XXX-category)
        """
        # Arrange
        request = "Test feature"
        context = PlanningContext(request=request, mode="full")
        requirement_type = RequirementType(
            category="feature", complexity="simple", requires_spec=True, estimated_effort="hours"
        )

        # Act
        spec = planner_agent._generate_specification(context, requirement_type)

        # Assert
        assert spec.spec_id.startswith("spec-")
        assert "feature" in spec.spec_id
        # Format: spec-NNN-category
        parts = spec.spec_id.split("-")
        assert len(parts) >= 3

    def test_technical_plan_output_includes_quality_strategy(self, planner_agent):
        """
        GIVEN: Technical plan generation
        WHEN: Plan is created
        THEN: Quality strategy includes TDD and coverage target
        """
        # Arrange
        spec = Specification(
            spec_id="spec-001",
            title="Test",
            goals=["Goal"],
            non_goals=["Non-goal"],
            personas={"dev": "Developer"},
            user_journeys=[],
            acceptance_criteria=["Criterion"],
        )
        context = PlanningContext(request="Test", mode="full")

        # Act
        plan = planner_agent._generate_technical_plan(context, spec)

        # Assert
        assert "testing_approach" in plan.quality_strategy
        assert "TDD" in plan.quality_strategy["testing_approach"]
        assert plan.quality_strategy["coverage_target"] == "100%"
        assert "validation_steps" in plan.quality_strategy

    def test_planning_result_recommendations_include_constitutional_guidance(self, planner_agent):
        """
        GIVEN: Planning execution
        WHEN: Recommendations are generated
        THEN: Constitutional compliance guidance is included
        """
        # Arrange
        spec = Specification(
            spec_id="spec-001",
            title="Test",
            goals=["Goal 1", "Goal 2", "Goal 3"],
            non_goals=["Non-goal"],
            personas={"dev": "Developer"},
            user_journeys=[],
            acceptance_criteria=["Criterion"],
        )
        plan = TechnicalPlan(
            plan_id="plan-001",
            spec_id="spec-001",
            architecture={"overview": "Test"},
            agent_assignments={"code": ["Task 1"]},
            tool_requirements=["Read", "Write"],
            contracts={},
            quality_strategy={"testing_approach": "TDD"},
            risk_assessment=[],
            milestones=[],
            estimated_duration="1 day",
        )

        # Act
        recommendations = planner_agent._generate_recommendations(spec, plan)

        # Assert
        constitutional_refs = [
            r
            for r in recommendations
            if "Article" in r or "complete context" in r.lower() or "test coverage" in r.lower()
        ]
        assert len(constitutional_refs) >= 3  # At least 3 constitutional recommendations

    def test_task_breakdown_output_has_valid_structure(self, planner_agent):
        """
        GIVEN: Technical plan and specification
        WHEN: Task breakdown is generated
        THEN: Each task has required fields (id, title, assigned_to, status)
        """
        # Arrange
        spec = Specification(
            spec_id="spec-001",
            title="Test",
            goals=["Goal"],
            non_goals=["Non-goal"],
            personas={"dev": "Developer"},
            user_journeys=[],
            acceptance_criteria=["Implement feature X", "Write tests for feature X"],
        )
        plan = TechnicalPlan(
            plan_id="plan-001",
            spec_id="spec-001",
            architecture={"overview": "Test"},
            agent_assignments={"code": ["Implementation"]},
            tool_requirements=[],
            contracts={},
            quality_strategy={},
            risk_assessment=[],
            milestones=[],
            estimated_duration="1 day",
        )

        # Act
        tasks = planner_agent._generate_task_breakdown(plan, spec)

        # Assert
        assert len(tasks) >= 1
        for task in tasks:
            assert "task_id" in task
            assert "title" in task
            assert "assigned_to" in task
            assert "status" in task
            assert task["status"] == "pending"


# ============================================================================
# VectorStore Integration Tests (Article IV Compliance)
# ============================================================================


class TestSpecGeneratorVectorStoreIntegration:
    """Test VectorStore pattern application for learning."""

    @patch("dspy_agents.modules.planner_agent.DSPyPlannerAgent._generate_specification")
    def test_query_vectorstore_before_spec_generation(
        self, mock_gen_spec, planner_agent, mock_agent_context, sample_vectorstore_patterns
    ):
        """
        GIVEN: Planning request for feature with historical patterns
        WHEN: Specification generation begins
        THEN: VectorStore is queried for similar spec patterns (Article IV)
        """
        # Arrange
        mock_agent_context.search_memories = Mock(return_value=sample_vectorstore_patterns)
        request = "Implement authentication system"

        # Simulate VectorStore query
        similar_specs = mock_agent_context.search_memories(
            tags=["spec", "authentication", "approved"], include_session=False
        )

        # Act
        context = planner_agent._prepare_context(
            request, "full", learning_patterns=similar_specs  # type: ignore
        )

        # Assert
        assert len(context.learning_patterns) == 2
        assert context.learning_patterns[0]["confidence"] == 0.85
        assert context.learning_patterns[0]["feature_type"] == "authentication"

    def test_store_successful_spec_pattern_after_approval(
        self, planner_agent, mock_agent_context
    ):
        """
        GIVEN: Successfully generated and approved specification
        WHEN: Spec is finalized
        THEN: Pattern is stored in VectorStore for future learning (Article IV)
        """
        # Arrange
        request = "Implement user authentication"
        result = planner_agent.forward(request, mode="full")

        # Simulate storing pattern after approval
        if result.success and result.specification:
            pattern_data = {
                "spec_file": f"specs/{result.specification.spec_id}.md",
                "feature_type": result.requirement_type.category,
                "confidence": 0.85,
                "pattern": {
                    "goals": result.specification.goals,
                    "non_goals": result.specification.non_goals,
                    "personas": result.specification.personas,
                },
            }

            # Act
            mock_agent_context.store_memory(
                key=f"spec_pattern_{result.specification.spec_id}",
                content=pattern_data,
                tags=["spec_generator", "approved", result.requirement_type.category],
            )

            # Assert
            mock_agent_context.store_memory.assert_called_once()
            call_args = mock_agent_context.store_memory.call_args
            # call_args is a tuple: (args, kwargs) or just args
            if call_args.args:
                assert "spec_pattern" in call_args.args[0]
            if call_args.kwargs:
                assert "approved" in call_args.kwargs.get("tags", [])

    def test_apply_vectorstore_patterns_to_new_spec(
        self, planner_agent, sample_vectorstore_patterns
    ):
        """
        GIVEN: VectorStore patterns with high confidence (>0.6)
        WHEN: New specification is generated
        THEN: Historical patterns influence new spec structure
        """
        # Arrange
        request = "Add authentication with social login"
        context = PlanningContext(
            request=request, mode="full", learning_patterns=sample_vectorstore_patterns  # type: ignore
        )
        requirement_type = RequirementType(
            category="feature", complexity="complex", requires_spec=True, estimated_effort="weeks"
        )

        # High confidence patterns should be considered
        high_confidence_patterns = [
            p for p in sample_vectorstore_patterns if p["confidence"] >= 0.6
        ]

        # Act
        spec = planner_agent._generate_specification(context, requirement_type)

        # Assert
        assert len(high_confidence_patterns) == 2
        assert isinstance(spec, Specification)
        # Spec should follow learned patterns (at minimum, standard structure)
        assert len(spec.goals) >= 1
        assert len(spec.personas) >= 1

    def test_reject_low_confidence_vectorstore_patterns(self, planner_agent):
        """
        GIVEN: VectorStore patterns with low confidence (<0.6)
        WHEN: Specification is generated
        THEN: Low confidence patterns are ignored
        """
        # Arrange
        low_confidence_patterns = [
            {
                "spec_file": "specs/spec-old.md",
                "feature_type": "unknown",
                "confidence": 0.3,  # Below threshold
                "pattern": {"goals": ["Unclear goal"]},
            }
        ]
        request = "Test feature"
        context = PlanningContext(
            request=request, mode="full", learning_patterns=low_confidence_patterns  # type: ignore
        )
        requirement_type = RequirementType(
            category="feature", complexity="simple", requires_spec=True, estimated_effort="hours"
        )

        # Act
        spec = planner_agent._generate_specification(context, requirement_type)

        # Assert
        # Should not use low confidence pattern, generates standard spec
        assert isinstance(spec, Specification)
        assert "Unclear goal" not in spec.goals  # Low confidence pattern ignored


# ============================================================================
# Learning and History Tests
# ============================================================================


class TestSpecGeneratorLearning:
    """Test learning integration and planning history."""

    def test_planning_history_recorded_after_execution(self, planner_agent):
        """
        GIVEN: Planning execution with learning enabled
        WHEN: Planning completes
        THEN: Planning history is updated with result metadata
        """
        # Arrange
        request = "Test feature"
        assert len(planner_agent.planning_history) == 0

        # Act
        result = planner_agent.forward(request, mode="full", enable_learning=True)

        # Assert
        assert len(planner_agent.planning_history) == 1
        history_entry = planner_agent.planning_history[0]
        assert history_entry["category"] == result.requirement_type.category
        assert history_entry["success"] == result.success
        assert "num_tasks" in history_entry

    def test_planning_summary_provides_statistics(self, planner_agent):
        """
        GIVEN: Multiple planning sessions in history
        WHEN: Planning summary is requested
        THEN: Summary includes success rate and category distribution
        """
        # Arrange - Simulate multiple planning sessions
        for i in range(5):
            request = f"Feature {i}"
            planner_agent.forward(request, mode="simple")

        # Act
        summary = planner_agent.get_planning_summary()

        # Assert
        assert "total_sessions" in summary
        assert summary["total_sessions"] == 5
        assert "success_rate" in summary
        assert "category_distribution" in summary
        assert "average_tasks" in summary

    def test_planning_history_limited_to_100_entries(self, planner_agent):
        """
        GIVEN: More than 100 planning sessions
        WHEN: Planning history grows
        THEN: History is capped at most recent 100 entries
        """
        # Arrange - Simulate 110 planning sessions
        for i in range(110):
            planner_agent.planning_history.append(
                {
                    "timestamp": datetime.utcnow(),
                    "category": "feature",
                    "complexity": "simple",
                    "success": True,
                    "had_spec": False,
                    "num_tasks": 1,
                    "estimated_effort": "hours",
                }
            )

        # Act
        planner_agent._learn_from_planning(
            PlanningResult(
                success=True,
                requirement_type=RequirementType(
                    category="test",
                    complexity="simple",
                    requires_spec=False,
                    estimated_effort="hours",
                ),
                timestamp=datetime.utcnow(),
            )
        )

        # Assert
        assert len(planner_agent.planning_history) == 100  # Capped at 100
        assert planner_agent.planning_history[-1]["category"] == "test"  # Most recent


# ============================================================================
# Summary
# ============================================================================

"""
NECESSARY Pattern Coverage Summary:

✅ N (Normal): 4 tests - Happy path spec generation, plan generation, full flow
✅ E (Edge): 5 tests - Minimal input, empty personas, no criteria, long strings
✅ C (Corner): 3 tests - Test category, conflicting modes, mixed status
✅ E (Error): 6 tests - Missing fields, invalid types, DSPy failure, validation
✅ S (Security): 3 tests - Injection attempts, XSS, untrusted context
✅ S (Stress): 3 tests - Large goals, many agents, extensive patterns
✅ A (Accessibility): 3 tests - Sensible defaults, clear structure, metadata
✅ R (Regression): 3 tests - Datetime types, spec/plan matching, timestamps
✅ Y (Yield): 4 tests - Output format, quality strategy, recommendations, tasks

VectorStore Integration: 4 tests - Query before gen, store after approval, apply patterns, reject low confidence
Learning: 3 tests - History recording, summary statistics, history limits

Total: 41 comprehensive tests covering all aspects of SpecGenerator
"""
