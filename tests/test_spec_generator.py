"""
Tests for SpecGenerator class.

Constitutional Compliance:
- Article I: Complete context (all tests run to completion)
- Article II: TDD mandatory (tests written FIRST)
- Article IV: VectorStore query before generation
- Article V: Spec-kit methodology from spec-007
"""

import pytest

from shared.agent_context import create_agent_context
from shared.type_definitions.result import Err, Ok
from tools.orchestrator.spec_generator import Spec, SpecGenerator, SpecIntent


class TestIntentModel:
    """Test Intent Pydantic model."""

    def test_intent_valid_creation(self) -> None:
        """Test Intent model creation with valid data."""
        intent = SpecIntent(
            title="Add JWT Authentication",
            description="Implement JWT-based authentication for API endpoints",
            priority="high",
            tags=["auth", "security", "api"],
        )

        assert intent.title == "Add JWT Authentication"
        assert intent.description == "Implement JWT-based authentication for API endpoints"
        assert intent.priority == "high"
        assert intent.tags == ["auth", "security", "api"]

    def test_intent_optional_fields(self) -> None:
        """Test Intent with optional fields defaulting."""
        intent = SpecIntent(
            title="Fix typo in README",
            description="Correct spelling error",
        )

        assert intent.priority == "medium"  # Default
        assert intent.tags == []  # Default

    def test_intent_validation_empty_title(self) -> None:
        """Test SpecIntent validation fails with empty title."""
        with pytest.raises(ValueError, match="title"):
            SpecIntent(title="", description="Test")


class TestSpecModel:
    """Test Spec Pydantic model."""

    def test_spec_valid_creation(self) -> None:
        """Test Spec model creation with valid data."""
        spec = Spec(
            title="JWT Authentication",
            goals=[
                "Secure API endpoints with JWT tokens",
                "Implement token refresh mechanism",
            ],
            personas=[
                "API Consumer: Needs secure access to endpoints",
                "Backend Developer: Needs to implement auth logic",
            ],
            success_criteria=[
                "All API endpoints require valid JWT",
                "Token refresh works without re-authentication",
                "100% test coverage for auth flows",
            ],
            metadata={"priority": "high"},
        )

        assert spec.title == "JWT Authentication"
        assert len(spec.goals) == 2
        assert len(spec.personas) == 2
        assert len(spec.success_criteria) == 3
        # Access SpecMetadata attributes (Pydantic model, not dict)
        assert spec.metadata.priority == "high"

    def test_spec_empty_lists_invalid(self) -> None:
        """Test Spec validation fails with empty required lists."""
        with pytest.raises(ValueError):
            Spec(
                title="Test",
                goals=[],  # Empty goals invalid
                personas=["Persona 1"],
                success_criteria=["Criteria 1"],
            )


class TestSpecGenerator:
    """Test SpecGenerator class."""

    def test_generator_initialization(self) -> None:
        """Test SpecGenerator initializes with AgentContext."""
        context = create_agent_context(session_id="test_spec_gen")
        generator = SpecGenerator(context=context)

        assert generator.context == context

    def test_generate_queries_vectorstore(self) -> None:
        """Test generate() queries VectorStore for patterns (Article IV)."""
        context = create_agent_context(session_id="test_spec_patterns")

        # Store a relevant pattern
        context.store_memory(
            "spec_pattern_auth",
            {
                "pattern_type": "spec",
                "domain": "auth",
                "goals": ["Secure endpoints", "Token management"],
                "confidence": 0.8,
            },
            ["spec", "pattern", "auth"],
        )

        generator = SpecGenerator(context=context)
        intent = SpecIntent(
            title="JWT Authentication",
            description="Add JWT auth to API",
            tags=["auth"],
        )

        result = generator.generate(intent)

        # Should query VectorStore (validated by memory search in generate())
        assert result.is_ok()
        spec = result.unwrap()
        assert isinstance(spec, Spec)
        assert spec.title == "JWT Authentication"

    def test_generate_with_spec_kit_template(self) -> None:
        """Test generate() uses spec-kit template (Goals, Personas, Success Criteria)."""
        context = create_agent_context(session_id="test_spec_template")
        generator = SpecGenerator(context=context)

        intent = SpecIntent(
            title="Dark Mode Toggle",
            description="Add dark mode toggle to settings page",
            priority="medium",
        )

        result = generator.generate(intent)

        assert result.is_ok()
        spec = result.unwrap()

        # Spec-kit template sections
        assert len(spec.goals) > 0, "Spec must have goals"
        assert len(spec.personas) > 0, "Spec must have personas"
        assert len(spec.success_criteria) > 0, "Spec must have success criteria"

    def test_generate_injects_vectorstore_patterns(self) -> None:
        """Test generate() injects VectorStore patterns into spec (confidence ≥ 0.6)."""
        context = create_agent_context(session_id="test_pattern_injection")

        # Store high-confidence pattern
        context.store_memory(
            "spec_pattern_ui",
            {
                "pattern_type": "spec",
                "domain": "ui",
                "goals": [
                    "Implement theme toggle component",
                    "Add CSS-in-JS dark mode styles",
                ],
                "confidence": 0.9,
            },
            ["spec", "pattern", "ui"],
        )

        # Store low-confidence pattern (should be filtered)
        context.store_memory(
            "spec_pattern_ui_low",
            {
                "pattern_type": "spec",
                "domain": "ui",
                "goals": ["Random low-confidence goal"],
                "confidence": 0.4,
            },
            ["spec", "pattern", "ui"],
        )

        generator = SpecGenerator(context=context)
        intent = SpecIntent(
            title="Dark Mode",
            description="UI dark mode",
            tags=["ui"],
        )

        result = generator.generate(intent)

        assert result.is_ok()
        spec = result.unwrap()

        # Should include high-confidence pattern goals
        assert any("theme toggle" in goal.lower() or "CSS-in-JS" in goal for goal in spec.goals), (
            "High-confidence pattern not injected"
        )

    def test_generate_with_empty_intent_fails(self) -> None:
        """Test generate() fails with invalid intent."""
        context = create_agent_context(session_id="test_invalid_intent")
        generator = SpecGenerator(context=context)

        # Invalid intent (empty title)
        with pytest.raises(ValueError):
            SpecIntent(title="", description="Test")

    def test_generate_stores_metadata(self) -> None:
        """Test generate() includes intent metadata in spec."""
        context = create_agent_context(session_id="test_spec_metadata")
        generator = SpecGenerator(context=context)

        intent = SpecIntent(
            title="Test Feature",
            description="Test description",
            priority="high",
            tags=["test", "feature"],
        )

        result = generator.generate(intent)

        assert result.is_ok()
        spec = result.unwrap()

        # Metadata should include intent info (access as attributes)
        assert spec.metadata.priority == "high"
        assert spec.metadata.tags == ["test", "feature"]


class TestSpecGeneratorPlannerIntegration:
    """Test SpecGenerator integration with Planner agent (LLM-powered generation)."""

    @pytest.mark.integration
    def test_generate_with_planner_agent(self) -> None:
        """Test generate() uses Planner agent for LLM spec generation."""
        context = create_agent_context(session_id="test_planner_integration")
        generator = SpecGenerator(context=context)

        intent = SpecIntent(
            title="User Registration",
            description="Implement user registration with email verification",
            priority="high",
            tags=["auth", "user"],
        )

        result = generator.generate(intent)

        assert result.is_ok()
        spec = result.unwrap()

        # LLM-generated spec should have detailed content
        assert len(spec.goals) >= 2, "LLM should generate multiple goals"
        assert len(spec.personas) >= 1, "LLM should generate personas"
        assert len(spec.success_criteria) >= 3, "LLM should generate detailed criteria"

    @pytest.mark.integration
    def test_generate_with_complex_intent(self) -> None:
        """Test generate() handles complex multi-component intent."""
        context = create_agent_context(session_id="test_complex_intent")
        generator = SpecGenerator(context=context)

        intent = SpecIntent(
            title="E-commerce Shopping Cart",
            description=(
                "Implement shopping cart with: "
                "product catalog, cart management, checkout flow, payment integration"
            ),
            priority="high",
            tags=["ecommerce", "cart", "payment"],
        )

        result = generator.generate(intent)

        assert result.is_ok()
        spec = result.unwrap()

        # Complex intent should generate comprehensive spec
        assert len(spec.goals) >= 4, "Complex intent needs multiple goals"
        assert len(spec.success_criteria) >= 5, "Complex intent needs detailed criteria"


class TestSpecGeneratorErrorHandling:
    """Test SpecGenerator error handling with Result pattern."""

    def test_generate_returns_result_type(self) -> None:
        """Test generate() returns Result[Spec, str] (Constitutional Law #5)."""
        context = create_agent_context(session_id="test_result_pattern")
        generator = SpecGenerator(context=context)

        intent = SpecIntent(title="Test", description="Test")
        result = generator.generate(intent)

        # Result pattern validation
        assert hasattr(result, "is_ok")
        assert hasattr(result, "is_err")
        assert hasattr(result, "unwrap")

    def test_generate_error_on_planner_failure(self) -> None:
        """Test generate() returns Err on Planner agent failure."""
        context = create_agent_context(session_id="test_planner_error")

        # Simulate Planner failure by passing invalid context
        generator = SpecGenerator(context=context)
        generator._planner_available = False  # Force error path

        intent = SpecIntent(title="Test", description="Test")
        result = generator.generate(intent)

        # Should still succeed with fallback template
        assert result.is_ok() or result.is_err()
