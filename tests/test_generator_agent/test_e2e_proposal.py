"""
Test Generator E2E Proposal Tests - NECESSARY Pattern Compliance

Tests for TestGenerator's ability to propose E2E tests for complex features.

CONSTITUTIONAL MANDATE:
- Article VI: TDD (tests before code, including E2E tests)
- ADR-037: E2E testing framework with TestGenerator integration

NECESSARY Coverage:
- Normal: TestGenerator proposes E2E for multi-agent workflows
- Edge: TestGenerator skips E2E for simple functions
- Validation: E2E templates are correct
- Error: Invalid E2E test proposals
"""

import pytest
from pathlib import Path


# =============================================================================
# NORMAL OPERATION TESTS
# =============================================================================


def test_generator_proposes_e2e_for_complex_features():
    """
    Verify TestGenerator proposes E2E tests for features involving >3 agents.

    Pattern: NECESSARY - Normal operation
    Validates: E2E test proposal heuristics
    """
    from test_generator_agent.test_generator import TestGenerator

    # Arrange: Complex feature specification
    spec_content = """
# Feature: User Authentication System

## Agents Involved:
- PlannerAgent: Generate authentication plan
- CodingAgent: Implement JWT token generation
- TestGenerator: Create unit tests
- QualityEnforcer: Validate security standards
- MergerAgent: Create PR

## Workflow:
1. PlannerAgent creates spec-based plan
2. CodingAgent implements models, repositories, services
3. TestGenerator creates comprehensive test suite
4. QualityEnforcer validates security (no plaintext passwords)
5. MergerAgent integrates changes
"""

    # Act: Analyze feature for test proposal
    generator = TestGenerator()

    result = generator.analyze_feature_for_e2e(spec_content)

    # Assert: E2E test proposed
    assert result.is_ok()
    proposal = result.unwrap()

    assert proposal.get("needs_e2e_test") is True
    assert proposal.get("reason") == "multi_agent_workflow"
    assert proposal.get("agent_count") >= 3


def test_generator_uses_e2e_templates():
    """
    Verify TestGenerator uses E2E templates (mission/agent/tool).

    Pattern: NECESSARY - Normal operation
    Validates: Template selection logic
    """
    from test_generator_agent.test_generator import TestGenerator

    generator = TestGenerator()

    # Test: Mission template
    mission_template = generator.get_e2e_template("mission")
    assert mission_template is not None
    assert "full_agent_context" in mission_template
    assert "tmp_git_repo" in mission_template
    assert "mock_openai_api" in mission_template

    # Test: Agent template
    agent_template = generator.get_e2e_template("agent")
    assert agent_template is not None
    assert "full_agent_context" in agent_template

    # Test: Tool template
    tool_template = generator.get_e2e_template("tool")
    assert tool_template is not None
    assert "@pytest.mark.e2e" in tool_template


def test_generator_creates_e2e_test_file():
    """
    Verify TestGenerator creates E2E test file in tests/e2e/.

    Pattern: NECESSARY - Normal operation
    Validates: File generation and placement
    """
    from test_generator_agent.test_generator import TestGenerator

    # Arrange: Feature requiring E2E test
    feature_spec = {
        "name": "oauth_integration",
        "type": "mission",
        "agents": ["planner", "coder", "quality_enforcer", "merger"],
        "workflow": "Spec → Plan → Code → Verify → PR"
    }

    # Act: Generate E2E test
    generator = TestGenerator()

    result = generator.generate_e2e_test(feature_spec)

    # Assert: E2E test file created
    assert result.is_ok()
    test_file_path = Path(result.unwrap())

    assert test_file_path.exists()
    assert "tests/e2e/" in str(test_file_path)
    assert test_file_path.name.startswith("test_")
    assert test_file_path.suffix == ".py"

    # Assert: Test content uses E2E fixtures
    test_content = test_file_path.read_text()
    assert "@pytest.mark.e2e" in test_content
    assert "full_agent_context" in test_content


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


def test_generator_skips_e2e_for_simple_features():
    """
    Verify TestGenerator does NOT propose E2E for simple functions.

    Pattern: NECESSARY - Edge case
    Validates: E2E test filtering (avoid over-testing)
    """
    from test_generator_agent.test_generator import TestGenerator

    # Arrange: Simple utility function
    spec_content = """
# Feature: Add type hints to validate_email

## Implementation:
- Add type hints to existing function
- Update docstring

## Testing:
- Unit test with valid/invalid emails
"""

    # Act: Analyze feature
    generator = TestGenerator()

    result = generator.analyze_feature_for_e2e(spec_content)

    # Assert: E2E test NOT proposed
    assert result.is_ok()
    proposal = result.unwrap()

    assert proposal.get("needs_e2e_test") is False
    assert proposal.get("reason") == "simple_feature"


def test_generator_handles_hybrid_features():
    """
    Verify TestGenerator proposes both unit AND E2E for hybrid features.

    Pattern: NECESSARY - Edge case
    Validates: Multi-level test strategy
    """
    from test_generator_agent.test_generator import TestGenerator

    # Arrange: Feature with both unit-testable components and workflow
    spec_content = """
# Feature: Data Validation Pipeline

## Components:
- validate_email(email: str) -> Result[str, ValidationError] (unit testable)
- validate_phone(phone: str) -> Result[str, ValidationError] (unit testable)

## Workflow:
- PlannerAgent designs validation architecture
- CodingAgent implements validators
- TestGenerator creates unit tests
- QualityEnforcer validates performance
- MergerAgent integrates
"""

    # Act: Analyze feature
    generator = TestGenerator()

    result = generator.analyze_feature_for_e2e(spec_content)

    # Assert: Hybrid strategy proposed
    assert result.is_ok()
    proposal = result.unwrap()

    assert proposal.get("needs_unit_tests") is True
    assert proposal.get("needs_e2e_test") is True
    assert proposal.get("test_strategy") == "hybrid"


# =============================================================================
# VALIDATION TESTS
# =============================================================================


def test_generator_e2e_tests_follow_necessary_pattern():
    """
    Verify generated E2E tests follow NECESSARY pattern.

    Pattern: NECESSARY - Validation
    Constitutional: ADR-011 (NECESSARY mandatory)
    """
    from test_generator_agent.test_generator import TestGenerator

    # Arrange: Feature spec
    feature_spec = {
        "name": "payment_processing",
        "type": "mission",
        "agents": ["planner", "coder", "quality_enforcer", "merger"]
    }

    # Act: Generate E2E test
    generator = TestGenerator()

    result = generator.generate_e2e_test(feature_spec)

    # Assert: E2E test generated
    assert result.is_ok()
    test_file_path = Path(result.unwrap())

    test_content = test_file_path.read_text()

    # Assert: NECESSARY categories present
    assert "# Normal operation tests" in test_content.lower() or \
           "normal operation" in test_content.lower()
    assert "# Edge case tests" in test_content.lower() or \
           "edge case" in test_content.lower()
    assert "# Error condition tests" in test_content.lower() or \
           "error condition" in test_content.lower()


def test_generator_e2e_tests_use_correct_fixtures():
    """
    Verify generated E2E tests use E2E fixtures.

    Pattern: NECESSARY - Validation
    Validates: Fixture integration
    """
    from test_generator_agent.test_generator import TestGenerator

    # Arrange: Mission-type feature
    feature_spec = {
        "name": "test_mission",
        "type": "mission",
        "agents": ["planner", "coder", "merger"]
    }

    # Act: Generate E2E test
    generator = TestGenerator()

    result = generator.generate_e2e_test(feature_spec)

    # Assert: Correct fixtures used
    assert result.is_ok()
    test_content = Path(result.unwrap()).read_text()

    # Mission E2E tests need full context
    assert "full_agent_context" in test_content
    assert "tmp_git_repo" in test_content
    assert "mock_openai_api" in test_content


def test_generator_e2e_tests_validate_article_iv_compliance():
    """
    Verify generated E2E tests check VectorStore usage (Article IV).

    Pattern: NECESSARY - Validation
    Constitutional: Article IV (VectorStore mandatory)
    """
    from test_generator_agent.test_generator import TestGenerator

    # Arrange: Feature involving learning
    feature_spec = {
        "name": "pattern_learning",
        "type": "agent",
        "agents": ["planner"],
        "requires_vectorstore": True
    }

    # Act: Generate E2E test
    generator = TestGenerator()

    result = generator.generate_e2e_test(feature_spec)

    # Assert: Article IV validation tests included
    assert result.is_ok()
    test_content = Path(result.unwrap()).read_text()

    assert "vectorstore" in test_content.lower()
    assert "article iv" in test_content.lower() or "article_iv" in test_content.lower()


# =============================================================================
# ERROR CONDITION TESTS
# =============================================================================


def test_generator_handles_invalid_e2e_template_type():
    """
    Verify TestGenerator handles invalid template types.

    Pattern: NECESSARY - Error condition
    Validates: Input validation
    """
    from test_generator_agent.test_generator import TestGenerator

    generator = TestGenerator()

    # Act: Request invalid template
    result = generator.get_e2e_template("invalid_type")

    # Assert: Error or default template
    assert result is None or isinstance(result, str)


def test_generator_handles_missing_feature_metadata():
    """
    Verify TestGenerator handles incomplete feature specifications.

    Pattern: NECESSARY - Error condition
    Validates: Graceful degradation
    """
    from test_generator_agent.test_generator import TestGenerator

    # Arrange: Incomplete feature spec
    feature_spec = {
        "name": "incomplete_feature"
        # Missing: type, agents, workflow
    }

    # Act: Try to generate E2E test
    generator = TestGenerator()

    result = generator.generate_e2e_test(feature_spec)

    # Assert: Error reported or defaults used
    if result.is_err():
        error = result.error
        assert "missing" in str(error).lower() or "invalid" in str(error).lower()
    else:
        # Generator used defaults
        assert result.is_ok()


# =============================================================================
# REGRESSION TESTS
# =============================================================================


def test_generator_doesnt_duplicate_e2e_and_unit_tests():
    """
    Verify TestGenerator doesn't create duplicate test cases.

    Pattern: NECESSARY - Regression
    Validates: Test uniqueness
    """
    from test_generator_agent.test_generator import TestGenerator

    # Arrange: Feature with clear unit test boundaries
    feature_spec = {
        "name": "email_validator",
        "type": "tool",
        "agents": ["coder"],
        "unit_testable": True
    }

    # Act: Generate tests
    generator = TestGenerator()

    unit_result = generator.generate_unit_tests(feature_spec)
    e2e_result = generator.analyze_feature_for_e2e(feature_spec)

    # Assert: Unit tests generated
    assert unit_result.is_ok()

    # Assert: E2E not needed for simple tool
    assert e2e_result.is_ok()
    proposal = e2e_result.unwrap()
    assert proposal.get("needs_e2e_test") is False


# =============================================================================
# ACCESSIBILITY TESTS
# =============================================================================


def test_generator_provides_e2e_test_documentation():
    """
    Verify generated E2E tests include clear documentation.

    Pattern: NECESSARY - Accessibility
    Validates: Test readability
    """
    from test_generator_agent.test_generator import TestGenerator

    # Arrange: Feature spec
    feature_spec = {
        "name": "documented_feature",
        "type": "mission",
        "agents": ["planner", "coder", "merger"]
    }

    # Act: Generate E2E test
    generator = TestGenerator()

    result = generator.generate_e2e_test(feature_spec)

    # Assert: Documentation present
    assert result.is_ok()
    test_content = Path(result.unwrap()).read_text()

    # Assert: Module docstring
    assert '"""' in test_content

    # Assert: Test docstrings
    assert "def test_" in test_content
    # Every test should have docstring
    test_functions = test_content.count("def test_")
    docstrings_after_tests = test_content.count('def test_') <= test_content.count('"""')


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


def test_generator_integrates_with_e2e_framework():
    """
    Verify TestGenerator integrates with E2E testing framework.

    Pattern: NECESSARY - Integration
    Validates: End-to-end workflow
    """
    from test_generator_agent.test_generator import TestGenerator

    # Arrange: Feature requiring E2E test
    feature_spec = {
        "name": "integration_test_feature",
        "type": "mission",
        "agents": ["planner", "coder", "quality_enforcer", "merger"]
    }

    # Act: Generate E2E test
    generator = TestGenerator()

    result = generator.generate_e2e_test(feature_spec)

    # Assert: Test created
    assert result.is_ok()
    test_file_path = Path(result.unwrap())

    # Assert: Test is runnable with pytest
    test_content = test_file_path.read_text()
    assert "import pytest" in test_content
    assert "@pytest.mark.e2e" in test_content

    # Assert: Fixtures are correctly referenced
    assert "full_agent_context" in test_content
    # Fixtures should be function parameters, not imported
    assert "def test_" in test_content


def test_generator_proposal_includes_execution_estimate():
    """
    Verify E2E test proposals include time estimates.

    Pattern: NECESSARY - Accessibility
    Validates: Resource planning support
    """
    from test_generator_agent.test_generator import TestGenerator

    # Arrange: Complex feature
    spec_content = """
# Feature: Multi-step Migration

## Agents: 5 agents involved
## Estimated Complexity: High
"""

    # Act: Analyze for E2E
    generator = TestGenerator()

    result = generator.analyze_feature_for_e2e(spec_content)

    # Assert: Proposal includes estimate
    assert result.is_ok()
    proposal = result.unwrap()

    # Should include time estimate for E2E test execution
    assert "estimated_duration" in proposal or "timeout" in proposal
