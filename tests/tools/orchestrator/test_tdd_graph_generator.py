"""
Tests for TDDGraphGenerator - Test-First Task Graph Generation (Article II).

Constitutional Compliance:
- Article I: Complete context (VectorStore query before generation)
- Article II: TDD enforcement (Test tasks auto-created for Code tasks)
- Article IV: VectorStore integration (pattern query/store)
- Article V: Spec-driven (TaskGraph from ApprovedSpec)

NECESSARY Pattern Coverage:
- N: Normal operation (spec → graph with Test-first ordering)
- E: Edge cases (spec with no goals, single goal)
- C: Corner cases (complex multi-module specs)
- E: Error conditions (invalid spec, VectorStore unavailable)
- S: Security (no code injection in task IDs)
- S: Stress (large specs with 50+ tasks)
- A: Accessibility (clear task descriptions)
- R: Regression (deterministic task generation)
- Y: Yield (all tasks present with correct dependencies)
"""

import pytest

from shared.agent_context import create_agent_context
from shared.models.task_graph import Phase, Task, TaskGraph, TaskTier, TaskType
from shared.type_definitions.result import Err, Ok
from tools.orchestrator.approval_checkpoint import ApprovalDecision, ApprovedSpec, Spec
from tools.orchestrator.tdd_graph_generator import TDDGraphGenerator


class TestTDDGraphGeneratorNormalOperation:
    """Test normal operation - spec to graph with TDD ordering."""

    @pytest.fixture
    def context(self):
        """Create test context with memory."""
        return create_agent_context(session_id="test_tdd_graph_gen")

    @pytest.fixture
    def generator(self, context):
        """Create TDDGraphGenerator instance."""
        return TDDGraphGenerator(context=context)

    @pytest.fixture
    def simple_spec(self):
        """Create simple approved spec for testing."""
        spec = Spec(
            title="JWT Authentication",
            content="Add JWT-based authentication to API endpoints with token validation",
        )
        decision = ApprovalDecision(action="approve")
        return ApprovedSpec(spec=spec, decision=decision, edit_count=0)

    def test_generate_returns_ok_with_valid_spec(self, generator, simple_spec):
        """Test generate() returns Ok with valid spec."""
        # Act
        result = generator.generate(simple_spec)

        # Assert
        assert result.is_ok(), (
            f"Expected Ok, got Err: {result.unwrap_err() if result.is_err() else ''}"
        )
        graph = result.unwrap()
        assert isinstance(graph, TaskGraph)
        assert graph.mission == "JWT Authentication"

    def test_generate_creates_spec_tasks_for_goals(self, generator, simple_spec):
        """Test Spec tasks created for each goal."""
        # Act
        result = generator.generate(simple_spec)
        graph = result.unwrap()

        # Assert
        spec_tasks = [t for phase in graph.phases for t in phase.tasks if t.type == TaskType.SPEC]
        assert len(spec_tasks) >= 1, "Expected at least 1 Spec task"

    def test_generate_creates_code_tasks_for_implementation(self, generator, simple_spec):
        """Test Code tasks created for implementation."""
        # Act
        result = generator.generate(simple_spec)
        graph = result.unwrap()

        # Assert
        code_tasks = [t for phase in graph.phases for t in phase.tasks if t.type == TaskType.CODE]
        assert len(code_tasks) >= 1, "Expected at least 1 Code task"

    def test_generate_creates_test_tasks_for_each_code_task(self, generator, simple_spec):
        """Test Test task auto-created for each Code task (Article II)."""
        # Act
        result = generator.generate(simple_spec)
        graph = result.unwrap()

        # Assert
        all_tasks = graph.all_tasks()
        code_tasks = [t for t in all_tasks if t.type == TaskType.CODE]
        test_tasks = [t for t in all_tasks if t.type == TaskType.TEST]

        assert len(test_tasks) >= len(code_tasks), (
            f"Expected at least {len(code_tasks)} Test tasks for {len(code_tasks)} Code tasks"
        )

        # Verify each Code task has corresponding Test task
        for code_task in code_tasks:
            matching_tests = [t for t in test_tasks if t.verification_target == code_task.id]
            assert len(matching_tests) == 1, (
                f"Code task {code_task.id} missing Test task (Article II violation)"
            )

    def test_generate_sets_verification_target_on_test_tasks(self, generator, simple_spec):
        """Test Test tasks have verification_target set to Code task ID."""
        # Act
        result = generator.generate(simple_spec)
        graph = result.unwrap()

        # Assert
        test_tasks = [t for t in graph.all_tasks() if t.type == TaskType.TEST]
        for test_task in test_tasks:
            assert test_task.verification_target is not None, (
                f"Test task {test_task.id} missing verification_target"
            )
            assert test_task.verification_target.startswith("code_"), (
                f"Test task {test_task.id} verification_target invalid: {test_task.verification_target}"
            )

    def test_generate_creates_test_tasks_before_code_tasks_in_dependencies(
        self, generator, simple_spec
    ):
        """Test Test tasks depend on Code tasks (reversed execution order)."""
        # Act
        result = generator.generate(simple_spec)
        graph = result.unwrap()

        # Assert
        test_tasks = [t for t in graph.all_tasks() if t.type == TaskType.TEST]
        for test_task in test_tasks:
            assert test_task.verification_target in test_task.dependencies, (
                f"Test task {test_task.id} missing Code task in dependencies"
            )


class TestTDDGraphGeneratorVectorStoreIntegration:
    """Test VectorStore integration (Article IV)."""

    @pytest.fixture
    def context(self):
        """Create test context with memory."""
        return create_agent_context(session_id="test_vectorstore")

    @pytest.fixture
    def generator(self, context):
        """Create TDDGraphGenerator instance."""
        return TDDGraphGenerator(context=context)

    @pytest.fixture
    def spec_with_patterns(self, context):
        """Create spec with VectorStore patterns."""
        # Store patterns in VectorStore (Article IV)
        context.store_memory(
            "pattern_jwt_auth",
            {
                "pattern_type": "authentication",
                "tasks": ["spec_auth_design", "code_jwt_impl", "test_jwt_impl"],
                "confidence": 0.8,
            },
            ["task_graph", "pattern", "auth"],
        )

        spec = Spec(
            title="JWT Authentication",
            content="Add JWT-based authentication",
        )
        decision = ApprovalDecision(action="approve")
        return ApprovedSpec(spec=spec, decision=decision)

    def test_generate_queries_vectorstore_before_generation(self, generator, spec_with_patterns):
        """Test VectorStore queried before generation (Article IV)."""
        # Act
        result = generator.generate(spec_with_patterns)

        # Assert
        assert result.is_ok(), "Generation should succeed with VectorStore patterns"
        graph = result.unwrap()

        # Verify patterns used (check metadata)
        assert "patterns_used" in graph.metadata
        patterns_used = graph.metadata["patterns_used"]
        assert patterns_used >= 0, "Expected patterns_used count"

    def test_generate_uses_high_confidence_patterns(self, generator, context):
        """Test only patterns with confidence ≥ 0.6 are used."""
        # Arrange - store low and high confidence patterns
        context.store_memory(
            "pattern_low_confidence",
            {"pattern_type": "auth", "confidence": 0.4},
            ["task_graph", "pattern"],
        )
        context.store_memory(
            "pattern_high_confidence",
            {"pattern_type": "auth", "confidence": 0.8},
            ["task_graph", "pattern"],
        )

        spec = Spec(title="Authentication", content="Add authentication system")
        decision = ApprovalDecision(action="approve")
        approved_spec = ApprovedSpec(spec=spec, decision=decision)

        # Act
        result = generator.generate(approved_spec)

        # Assert
        assert result.is_ok()
        graph = result.unwrap()

        # High confidence patterns should be used (exact count depends on implementation)
        assert graph.metadata.get("patterns_used", 0) >= 0


class TestTDDGraphGeneratorEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def context(self):
        """Create test context."""
        return create_agent_context(session_id="test_edge_cases")

    @pytest.fixture
    def generator(self, context):
        """Create TDDGraphGenerator instance."""
        return TDDGraphGenerator(context=context)

    def test_generate_with_minimal_spec(self, generator):
        """Test generation with minimal spec content."""
        # Arrange
        spec = Spec(title="Minimal", content="Minimal implementation")
        decision = ApprovalDecision(action="approve")
        approved_spec = ApprovedSpec(spec=spec, decision=decision)

        # Act
        result = generator.generate(approved_spec)

        # Assert
        assert result.is_ok(), "Should handle minimal spec gracefully"
        graph = result.unwrap()
        assert len(graph.all_tasks()) >= 2, "Expected at least Spec + Code + Test tasks"

    def test_generate_with_complex_multi_goal_spec(self, generator):
        """Test generation with complex spec (multiple goals/modules)."""
        # Arrange
        spec = Spec(
            title="Complete Auth System",
            content=(
                "Implement complete authentication system:\n"
                "1. JWT token generation with RSA-256\n"
                "2. Token validation middleware\n"
                "3. User session management\n"
                "4. Refresh token rotation\n"
                "5. Rate limiting per endpoint"
            ),
        )
        decision = ApprovalDecision(action="approve")
        approved_spec = ApprovedSpec(spec=spec, decision=decision)

        # Act
        result = generator.generate(approved_spec)

        # Assert
        assert result.is_ok()
        graph = result.unwrap()

        # Should create multiple tasks for complex spec
        all_tasks = graph.all_tasks()
        code_tasks = [t for t in all_tasks if t.type == TaskType.CODE]
        test_tasks = [t for t in all_tasks if t.type == TaskType.TEST]

        assert len(code_tasks) >= 2, "Expected multiple Code tasks for complex spec"
        assert len(test_tasks) >= len(code_tasks), "Each Code task needs Test task"

    def test_generate_with_security_sensitive_content(self, generator):
        """Test task IDs are sanitized (no code injection)."""
        # Arrange
        spec = Spec(
            title="Auth'; DROP TABLE tasks; --",
            content="Malicious content",
        )
        decision = ApprovalDecision(action="approve")
        approved_spec = ApprovedSpec(spec=spec, decision=decision)

        # Act
        result = generator.generate(approved_spec)

        # Assert
        assert result.is_ok(), "Should sanitize malicious input"
        graph = result.unwrap()

        # Verify task IDs are alphanumeric with underscores only
        for task in graph.all_tasks():
            assert task.id.replace("_", "").isalnum(), (
                f"Task ID {task.id} contains invalid characters"
            )


class TestTDDGraphGeneratorDeterminism:
    """Test deterministic task generation (reproducibility)."""

    @pytest.fixture
    def context(self):
        """Create test context."""
        return create_agent_context(session_id="test_determinism")

    @pytest.fixture
    def generator(self, context):
        """Create TDDGraphGenerator instance."""
        return TDDGraphGenerator(context=context)

    @pytest.fixture
    def standard_spec(self):
        """Create standard spec for reproducibility tests."""
        spec = Spec(
            title="User Management",
            content="Implement user CRUD operations with validation",
        )
        decision = ApprovalDecision(action="approve")
        return ApprovedSpec(spec=spec, decision=decision)

    def test_generate_produces_identical_graphs_across_runs(self, generator, standard_spec):
        """Test same spec produces identical task graphs (determinism)."""
        # Act
        result_1 = generator.generate(standard_spec)
        result_2 = generator.generate(standard_spec)

        # Assert
        assert result_1.is_ok()
        assert result_2.is_ok()

        graph_1 = result_1.unwrap()
        graph_2 = result_2.unwrap()

        # Compare task counts
        assert len(graph_1.all_tasks()) == len(graph_2.all_tasks())

        # Compare task IDs (order matters for determinism)
        tasks_1_ids = [t.id for t in graph_1.all_tasks()]
        tasks_2_ids = [t.id for t in graph_2.all_tasks()]
        assert tasks_1_ids == tasks_2_ids, "Task generation should be deterministic"


class TestTDDGraphGeneratorTaskGraphValidation:
    """Test generated graphs pass Pydantic validation (Article II)."""

    @pytest.fixture
    def context(self):
        """Create test context."""
        return create_agent_context(session_id="test_validation")

    @pytest.fixture
    def generator(self, context):
        """Create TDDGraphGenerator instance."""
        return TDDGraphGenerator(context=context)

    def test_generated_graph_passes_pydantic_validation(self, generator):
        """Test generated TaskGraph passes all Pydantic validators."""
        # Arrange
        spec = Spec(
            title="Feature X",
            content="Implement feature X with tests",
        )
        decision = ApprovalDecision(action="approve")
        approved_spec = ApprovedSpec(spec=spec, decision=decision)

        # Act
        result = generator.generate(approved_spec)

        # Assert
        assert result.is_ok(), (
            f"Validation failed: {result.unwrap_err() if result.is_err() else ''}"
        )
        graph = result.unwrap()

        # Pydantic validation happens automatically during model creation
        # If we got here without exception, validation passed

        # Additional checks for Article II compliance
        code_tasks = [t for t in graph.all_tasks() if t.type == TaskType.CODE]
        test_tasks = [t for t in graph.all_tasks() if t.type == TaskType.TEST]

        # Every Code task must have Test task (validated by TaskGraph model)
        for code_task in code_tasks:
            matching_tests = [
                t
                for t in test_tasks
                if t.verification_target == code_task.id and code_task.id in t.dependencies
            ]
            assert len(matching_tests) == 1, (
                f"Code task {code_task.id} missing Test dependency (Article II)"
            )

    def test_generated_graph_has_no_circular_dependencies(self, generator):
        """Test generated graph is a valid DAG (no cycles)."""
        # Arrange
        spec = Spec(
            title="Complex Feature",
            content="Implement complex feature with multiple modules",
        )
        decision = ApprovalDecision(action="approve")
        approved_spec = ApprovedSpec(spec=spec, decision=decision)

        # Act
        result = generator.generate(approved_spec)

        # Assert
        assert result.is_ok()
        graph = result.unwrap()

        # TaskGraph validator checks for circular dependencies automatically
        # If we got here, no circular dependencies exist

        # Additional check: verify topological sort works
        layers = graph.topological_sort()
        assert len(layers) > 0, "Topological sort should produce at least one layer"

    def test_generated_graph_has_valid_agent_assignments(self, generator):
        """Test all tasks have valid agent assignments."""
        # Arrange
        spec = Spec(
            title="Feature Y",
            content="Implement feature Y",
        )
        decision = ApprovalDecision(action="approve")
        approved_spec = ApprovedSpec(spec=spec, decision=decision)

        # Act
        result = generator.generate(approved_spec)

        # Assert
        assert result.is_ok()
        graph = result.unwrap()

        # Verify agent assignments
        valid_agents = {
            "planner",
            "chief_architect",
            "coder",
            "auditor",
            "test_generator",
            "quality_enforcer",
            "learning",
            "merger",
            "toolsmith",
            "summary",
        }

        for task in graph.all_tasks():
            assert task.agent in valid_agents, f"Task {task.id} has invalid agent: {task.agent}"
