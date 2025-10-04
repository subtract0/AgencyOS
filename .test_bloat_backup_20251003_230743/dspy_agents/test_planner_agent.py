"""
Comprehensive tests for DSPyPlannerAgent.

Tests follow the NECESSARY pattern and work with or without DSPy.
"""

from pathlib import Path
from unittest.mock import patch

from dspy_agents.modules.planner_agent import (
    DSPyPlannerAgent,
    PlanningContext,
    PlanningResult,
    RequirementType,
    Specification,
    TechnicalPlan,
    create_dspy_planner_agent,
)

# ===========================
# N - Named: Agent Initialization Tests
# ===========================


class TestDSPyPlannerAgentInitialization:
    """Test agent creation and initialization."""

    def test_agent_initialization_with_defaults(self):
        """Test agent initialization with default parameters."""
        agent = DSPyPlannerAgent()

        assert agent.model == "gpt-4o-mini"
        assert agent.reasoning_effort == "high"
        assert agent.enable_learning is True
        assert agent.specs_dir == Path("specs")
        assert agent.plans_dir == Path("plans")

    def test_agent_initialization_with_custom_params(self):
        """Test agent initialization with custom parameters."""
        agent = DSPyPlannerAgent(
            model="gpt-4",
            reasoning_effort="low",
            enable_learning=False,
            specs_dir="custom_specs",
            plans_dir="custom_plans",
        )

        assert agent.model == "gpt-4"
        assert agent.reasoning_effort == "low"
        assert agent.enable_learning is False
        assert agent.specs_dir == Path("custom_specs")
        assert agent.plans_dir == Path("custom_plans")

    def test_directories_created_on_init(self, tmp_path):
        """Test that spec and plan directories are created."""
        specs_dir = tmp_path / "test_specs"
        plans_dir = tmp_path / "test_plans"

        agent = DSPyPlannerAgent(specs_dir=str(specs_dir), plans_dir=str(plans_dir))

        assert specs_dir.exists()
        assert plans_dir.exists()

    def test_factory_function_creates_agent(self):
        """Test the factory function creates agent properly."""
        agent = create_dspy_planner_agent(model="claude", reasoning_effort="medium")

        assert isinstance(agent, DSPyPlannerAgent)
        assert agent.model == "claude"
        assert agent.reasoning_effort == "medium"


# ===========================
# E - Executable: Forward Method Tests
# ===========================


class TestForwardMethod:
    """Test main execution method."""

    def test_forward_simple_task(self):
        """Test forward method with simple task."""
        agent = DSPyPlannerAgent()

        result = agent.forward("Fix a typo in the README", mode="simple")

        assert isinstance(result, PlanningResult)
        assert result.success is True
        assert result.requirement_type.complexity == "simple"
        assert result.guidance is not None

    def test_forward_complex_task(self):
        """Test forward method with complex task requiring spec."""
        agent = DSPyPlannerAgent()

        result = agent.forward(
            "Implement a comprehensive user authentication system with OAuth2, JWT tokens, role-based access control, and audit logging",
            mode="full",
        )

        assert isinstance(result, PlanningResult)
        assert result.requirement_type.complexity == "complex"
        assert result.requirement_type.requires_spec is True

    def test_forward_with_learning_enabled(self):
        """Test that learning occurs when enabled."""
        agent = DSPyPlannerAgent(enable_learning=True)

        # Execute planning
        agent.forward("Create a new feature")

        # Check learning history
        assert len(agent.planning_history) == 1
        assert "category" in agent.planning_history[0]

    def test_forward_with_learning_disabled(self):
        """Test that no learning occurs when disabled."""
        agent = DSPyPlannerAgent(enable_learning=False)

        # Execute planning
        agent.forward("Create a new feature")

        # Check no learning history
        assert len(agent.planning_history) == 0

    def test_forward_handles_exceptions(self):
        """Test forward method handles exceptions gracefully."""
        agent = DSPyPlannerAgent()

        # Mock to return a failed result from spec-kit process
        failed_result = PlanningResult(
            success=False,
            requirement_type=RequirementType(
                category="feature",
                complexity="complex",
                requires_spec=True,
                estimated_effort="weeks",
            ),
            recommendations=["Planning failed: Test error"],
        )

        with patch.object(agent, "_execute_spec_kit_process", return_value=failed_result):
            # Use a complex task that requires spec
            result = agent.forward(
                "Implement a comprehensive user authentication system with OAuth2"
            )

            # Should return the failed result
            assert isinstance(result, PlanningResult)
            assert result.success is False
            assert "Planning failed" in result.recommendations[0]


# ===========================
# C - Comprehensive: Classification Tests
# ===========================


class TestRequirementClassification:
    """Test requirement classification functionality."""

    def test_classify_feature_requirement(self):
        """Test classification of feature requests."""
        agent = DSPyPlannerAgent()
        context = PlanningContext(request="Add user authentication feature")

        req_type = agent._classify_requirement(context)

        assert req_type.category == "feature"
        assert req_type.requires_spec is True

    def test_classify_bugfix_requirement(self):
        """Test classification of bug fixes."""
        agent = DSPyPlannerAgent()
        context = PlanningContext(request="Fix login error")

        req_type = agent._classify_requirement(context)

        assert req_type.category == "bugfix"
        assert req_type.complexity == "simple"
        assert req_type.requires_spec is False

    def test_classify_refactor_requirement(self):
        """Test classification of refactoring tasks."""
        agent = DSPyPlannerAgent()
        context = PlanningContext(request="Refactor database connection code")

        req_type = agent._classify_requirement(context)

        assert req_type.category == "refactor"

    def test_classify_docs_requirement(self):
        """Test classification of documentation tasks."""
        agent = DSPyPlannerAgent()
        context = PlanningContext(request="Document the API endpoints")

        req_type = agent._classify_requirement(context)

        assert req_type.category == "docs"
        assert req_type.requires_spec is False

    def test_classify_test_requirement(self):
        """Test classification of testing tasks."""
        agent = DSPyPlannerAgent()
        context = PlanningContext(request="Write unit tests for the API")

        req_type = agent._classify_requirement(context)

        assert req_type.category == "test"

    def test_classify_complexity_based_on_length(self):
        """Test complexity classification based on request length."""
        agent = DSPyPlannerAgent()

        # Short request
        short_context = PlanningContext(request="Fix bug")
        short_type = agent._classify_requirement(short_context)
        assert short_type.complexity == "simple"

        # Long request
        long_request = " ".join(["requirement"] * 60)
        long_context = PlanningContext(request=long_request)
        long_type = agent._classify_requirement(long_context)
        assert long_type.complexity == "complex"


# ===========================
# E - Edge Cases: Specification Generation Tests
# ===========================


class TestSpecificationGeneration:
    """Test specification generation."""

    def test_generate_specification_basic(self):
        """Test basic specification generation."""
        agent = DSPyPlannerAgent()
        context = PlanningContext(request="Create user management system")
        req_type = RequirementType(
            category="feature", complexity="complex", requires_spec=True, estimated_effort="weeks"
        )

        spec = agent._generate_specification(context, req_type)

        assert isinstance(spec, Specification)
        assert spec.spec_id.startswith("spec-")
        assert len(spec.goals) > 0
        assert len(spec.acceptance_criteria) > 0

    def test_specification_includes_personas(self):
        """Test that specifications include user personas."""
        agent = DSPyPlannerAgent()
        context = PlanningContext(request="Build dashboard")
        req_type = RequirementType(
            category="feature", complexity="complex", requires_spec=True, estimated_effort="weeks"
        )

        spec = agent._generate_specification(context, req_type)

        assert "developer" in spec.personas
        assert "end_user" in spec.personas

    def test_specification_with_existing_specs(self):
        """Test spec generation considers existing specs."""
        agent = DSPyPlannerAgent()
        context = PlanningContext(
            request="Add feature", existing_specs=["spec-001-feature.md", "spec-002-bugfix.md"]
        )
        req_type = RequirementType(
            category="feature", complexity="complex", requires_spec=True, estimated_effort="days"
        )

        spec = agent._generate_specification(context, req_type)

        # Should increment spec number
        assert "003" in spec.spec_id

    def test_specification_with_constraints(self):
        """Test spec generation with constraints."""
        agent = DSPyPlannerAgent()
        context = PlanningContext(request="Add feature with performance requirements")
        req_type = RequirementType(
            category="feature", complexity="complex", requires_spec=True, estimated_effort="weeks"
        )

        spec = agent._generate_specification(context, req_type)

        assert isinstance(spec.constraints, list)
        assert isinstance(spec.assumptions, list)


# ===========================
# S - Stateful: Technical Plan Generation Tests
# ===========================


class TestTechnicalPlanGeneration:
    """Test technical plan generation."""

    def test_generate_technical_plan_basic(self):
        """Test basic technical plan generation."""
        agent = DSPyPlannerAgent()

        # Create test specification
        spec = Specification(
            spec_id="spec-001-test",
            title="Test Feature",
            goals=["Implement feature X", "Ensure quality"],
            non_goals=["Don't break existing"],
            personas={"dev": "Developer"},
            user_journeys=[],
            acceptance_criteria=["Feature works", "Tests pass"],
        )

        context = PlanningContext(request="Test")
        plan = agent._generate_technical_plan(context, spec)

        assert isinstance(plan, TechnicalPlan)
        assert plan.spec_id == spec.spec_id
        assert plan.plan_id == f"plan-{spec.spec_id}"

    def test_technical_plan_includes_architecture(self):
        """Test that plan includes architecture details."""
        agent = DSPyPlannerAgent()

        spec = Specification(
            spec_id="spec-002-arch",
            title="Architecture Test",
            goals=["Design system"],
            non_goals=[],
            personas={},
            user_journeys=[],
            acceptance_criteria=[],
        )

        context = PlanningContext(request="Test")
        plan = agent._generate_technical_plan(context, spec)

        assert "overview" in plan.architecture
        assert "components" in plan.architecture

    def test_technical_plan_agent_assignments(self):
        """Test agent assignments in technical plan."""
        agent = DSPyPlannerAgent()

        spec = Specification(
            spec_id="spec-003-agents",
            title="Agent Test",
            goals=["Test agents"],
            non_goals=[],
            personas={},
            user_journeys=[],
            acceptance_criteria=[],
        )

        context = PlanningContext(request="Test")
        plan = agent._generate_technical_plan(context, spec)

        assert "code" in plan.agent_assignments
        assert "auditor" in plan.agent_assignments
        assert "test_generator" in plan.agent_assignments

    def test_technical_plan_quality_strategy(self):
        """Test quality strategy in technical plan."""
        agent = DSPyPlannerAgent()

        spec = Specification(
            spec_id="spec-004-quality",
            title="Quality Test",
            goals=["Ensure quality"],
            non_goals=[],
            personas={},
            user_journeys=[],
            acceptance_criteria=["100% test coverage"],
        )

        context = PlanningContext(request="Test")
        plan = agent._generate_technical_plan(context, spec)

        assert "testing_approach" in plan.quality_strategy
        assert plan.quality_strategy["coverage_target"] == "100%"


# ===========================
# S - Side Effects: Task Breakdown Tests
# ===========================


class TestTaskBreakdown:
    """Test task breakdown generation."""

    def test_generate_task_breakdown_from_plan(self):
        """Test generating tasks from technical plan."""
        agent = DSPyPlannerAgent()

        spec = Specification(
            spec_id="spec-005-tasks",
            title="Task Test",
            goals=["Goal 1", "Goal 2"],
            non_goals=[],
            personas={},
            user_journeys=[],
            acceptance_criteria=["Criterion 1", "Criterion 2"],
        )

        plan = TechnicalPlan(
            plan_id="plan-005",
            spec_id=spec.spec_id,
            architecture={"overview": "Test architecture"},
            agent_assignments={"code": ["implement"]},
            tool_requirements=["tool1"],
            contracts={},
            quality_strategy={},
            risk_assessment=[],
            milestones=[],
            estimated_duration="1 week",
        )

        tasks = agent._generate_task_breakdown(plan, spec)

        assert len(tasks) > 0
        assert all("task_id" in task for task in tasks)
        assert all("status" in task for task in tasks)

    def test_task_breakdown_includes_dependencies(self):
        """Test that tasks have proper dependencies."""
        agent = DSPyPlannerAgent()

        spec = Specification(
            spec_id="spec-006-deps",
            title="Dependency Test",
            goals=["Step 1", "Step 2", "Step 3"],
            non_goals=[],
            personas={},
            user_journeys=[],
            acceptance_criteria=["A", "B", "C"],
        )

        plan = TechnicalPlan(
            plan_id="plan-006",
            spec_id=spec.spec_id,
            architecture={"overview": "Sequential tasks"},
            agent_assignments={"code": ["all"]},
            tool_requirements=[],
            contracts={},
            quality_strategy={},
            risk_assessment=[],
            milestones=[],
            estimated_duration="3 days",
        )

        tasks = agent._generate_task_breakdown(plan, spec)

        # First task should have no dependencies
        assert tasks[0]["dependencies"] == []

        # Later tasks should depend on previous
        if len(tasks) > 1:
            assert len(tasks[1]["dependencies"]) > 0


# ===========================
# A - Async-style: Guidance Generation Tests
# ===========================


class TestGuidanceGeneration:
    """Test guidance generation for simple tasks."""

    def test_generate_guidance_for_bugfix(self):
        """Test guidance generation for bug fixes."""
        agent = DSPyPlannerAgent()
        context = PlanningContext(request="Fix login bug")
        req_type = RequirementType(
            category="bugfix", complexity="simple", requires_spec=False, estimated_effort="hours"
        )

        guidance = agent._generate_guidance(context, req_type)

        assert "Steps to Fix" in guidance
        assert "Constitutional Compliance" in guidance

    def test_generate_guidance_for_docs(self):
        """Test guidance generation for documentation."""
        agent = DSPyPlannerAgent()
        context = PlanningContext(request="Document API")
        req_type = RequirementType(
            category="docs", complexity="simple", requires_spec=False, estimated_effort="hours"
        )

        guidance = agent._generate_guidance(context, req_type)

        assert "Documentation Steps" in guidance

    def test_generate_guidance_for_tests(self):
        """Test guidance generation for testing tasks."""
        agent = DSPyPlannerAgent()
        context = PlanningContext(request="Add unit tests")
        req_type = RequirementType(
            category="test", complexity="simple", requires_spec=False, estimated_effort="hours"
        )

        guidance = agent._generate_guidance(context, req_type)

        assert "Testing Steps" in guidance
        assert "NECESSARY" in guidance

    def test_guidance_includes_constitutional_requirements(self):
        """Test that guidance includes constitutional compliance."""
        agent = DSPyPlannerAgent()
        context = PlanningContext(request="Simple task")
        req_type = RequirementType(
            category="feature", complexity="simple", requires_spec=False, estimated_effort="hours"
        )

        guidance = agent._generate_guidance(context, req_type)

        assert "Article I" in guidance
        assert "Article II" in guidance
        assert "Article III" in guidance


# ===========================
# R - Regression: Spec-Kit Process Tests
# ===========================


class TestSpecKitProcess:
    """Test the complete spec-kit process."""

    def test_execute_spec_kit_process_success(self):
        """Test successful spec-kit process execution."""
        agent = DSPyPlannerAgent()
        context = PlanningContext(request="Build complex feature")
        req_type = RequirementType(
            category="feature", complexity="complex", requires_spec=True, estimated_effort="weeks"
        )

        result = agent._execute_spec_kit_process(context, req_type)

        assert result.success is True
        assert result.specification is not None
        assert result.technical_plan is not None
        assert len(result.tasks) > 0

    def test_spec_kit_process_handles_errors(self):
        """Test spec-kit process error handling."""
        agent = DSPyPlannerAgent()
        context = PlanningContext(request="Test")
        req_type = RequirementType(
            category="feature", complexity="complex", requires_spec=True, estimated_effort="weeks"
        )

        # Mock to raise error
        with patch.object(agent, "_generate_specification", side_effect=Exception("Test error")):
            result = agent._execute_spec_kit_process(context, req_type)

            assert result.success is False
            assert "Planning failed" in result.recommendations[0]

    def test_spec_kit_generates_recommendations(self):
        """Test that spec-kit process generates recommendations."""
        agent = DSPyPlannerAgent()
        context = PlanningContext(request="Create feature")
        req_type = RequirementType(
            category="feature", complexity="complex", requires_spec=True, estimated_effort="weeks"
        )

        result = agent._execute_spec_kit_process(context, req_type)

        assert len(result.recommendations) > 0
        # Should include constitutional recommendations
        assert any("Article" in rec for rec in result.recommendations)


# ===========================
# Y - Yielding: Learning System Tests
# ===========================


class TestLearningSystem:
    """Test learning functionality."""

    def test_learn_from_planning_stores_history(self):
        """Test that planning results are stored in history."""
        agent = DSPyPlannerAgent(enable_learning=True)

        result = PlanningResult(
            success=True,
            requirement_type=RequirementType(
                category="feature",
                complexity="complex",
                requires_spec=True,
                estimated_effort="days",
            ),
            tasks=[{"task": "Test"}],
        )

        agent._learn_from_planning(result)

        assert len(agent.planning_history) == 1
        assert agent.planning_history[0]["category"] == "feature"
        assert agent.planning_history[0]["success"] is True

    def test_learning_history_limited_size(self):
        """Test that learning history has size limit."""
        agent = DSPyPlannerAgent(enable_learning=True)

        # Add more than limit
        for i in range(105):
            result = PlanningResult(
                success=True,
                requirement_type=RequirementType(
                    category="feature",
                    complexity="simple",
                    requires_spec=False,
                    estimated_effort="hours",
                ),
                tasks=[],
            )
            agent._learn_from_planning(result)

        # Should be limited to 100
        assert len(agent.planning_history) == 100

    def test_get_planning_summary(self):
        """Test planning summary generation."""
        agent = DSPyPlannerAgent(enable_learning=True)

        # Add some planning history
        for i in range(10):
            result = PlanningResult(
                success=i % 2 == 0,  # Alternate success
                requirement_type=RequirementType(
                    category="feature" if i < 5 else "bugfix",
                    complexity="simple",
                    requires_spec=False,
                    estimated_effort="hours",
                ),
                tasks=[{"task": f"Task {i}"}],
            )
            agent._learn_from_planning(result)

        summary = agent.get_planning_summary()

        assert summary["total_sessions"] == 10
        assert summary["success_rate"] == 0.5
        assert "feature" in summary["category_distribution"]
        assert "bugfix" in summary["category_distribution"]

    def test_calculate_planning_trend(self):
        """Test planning trend calculation."""
        agent = DSPyPlannerAgent(enable_learning=True)

        # Add declining success pattern
        for i in range(10):
            result = PlanningResult(
                success=i < 5,  # First 5 successful, last 5 failed
                requirement_type=RequirementType(
                    category="feature",
                    complexity="simple",
                    requires_spec=False,
                    estimated_effort="hours",
                ),
                tasks=[],
            )
            agent._learn_from_planning(result)

        trend = agent._calculate_planning_trend()
        assert trend == "declining"


# ===========================
# Fallback Mode Tests
# ===========================


class TestFallbackMode:
    """Test behavior when DSPy is not available."""

    @patch("dspy_agents.modules.planner_agent.DSPY_AVAILABLE", False)
    def test_agent_works_without_dspy(self):
        """Test agent functions without DSPy."""
        agent = DSPyPlannerAgent()

        result = agent.forward("Create a feature")

        assert isinstance(result, PlanningResult)

    def test_fallback_understand(self):
        """Test fallback understanding method."""
        agent = DSPyPlannerAgent()

        result = agent._fallback_understand(request="Test request")

        assert hasattr(result, "understanding")
        assert hasattr(result, "assumptions")
        assert hasattr(result, "risks")

    def test_fallback_strategize(self):
        """Test fallback strategy method."""
        agent = DSPyPlannerAgent()

        result = agent._fallback_strategize()

        assert hasattr(result, "strategy")
        assert hasattr(result, "milestones")
        assert hasattr(result, "success_criteria")

    def test_fallback_breakdown(self):
        """Test fallback breakdown method."""
        agent = DSPyPlannerAgent()

        result = agent._fallback_breakdown()

        assert hasattr(result, "tasks")
        assert hasattr(result, "task_dependencies")
        assert hasattr(result, "estimated_duration")


# ===========================
# Helper Methods Tests
# ===========================


class TestHelperMethods:
    """Test helper methods."""

    def test_extract_goals_from_understanding(self):
        """Test goal extraction."""
        agent = DSPyPlannerAgent()

        goals = agent._extract_goals("Implement new feature and test it")

        assert len(goals) > 0
        assert any("implement" in goal.lower() for goal in goals)

    def test_define_non_goals(self):
        """Test non-goals definition."""
        agent = DSPyPlannerAgent()

        req_type = RequirementType(
            category="bugfix", complexity="simple", requires_spec=False, estimated_effort="hours"
        )

        non_goals = agent._define_non_goals(req_type)

        assert len(non_goals) > 0
        assert "Adding new features" in non_goals

    def test_create_personas(self):
        """Test persona creation."""
        agent = DSPyPlannerAgent()

        req_type = RequirementType(
            category="test", complexity="simple", requires_spec=False, estimated_effort="hours"
        )

        personas = agent._create_personas(req_type)

        assert "developer" in personas
        assert "end_user" in personas
        assert "qa_engineer" in personas

    def test_identify_tools(self):
        """Test tool identification."""
        agent = DSPyPlannerAgent()

        spec = Specification(
            spec_id="test",
            title="Test",
            goals=["Write tests", "Document code"],
            non_goals=[],
            personas={},
            user_journeys=[],
            acceptance_criteria=[],
        )

        tools = agent._identify_tools(spec)

        assert "pytest" in tools
        assert "markdown" in tools

    def test_estimate_duration(self):
        """Test duration estimation."""
        agent = DSPyPlannerAgent()

        # Few goals
        spec1 = Specification(
            spec_id="test1",
            title="Small",
            goals=["Goal 1"],
            non_goals=[],
            personas={},
            user_journeys=[],
            acceptance_criteria=[],
        )

        duration1 = agent._estimate_duration(spec1)
        assert "1-2 days" in duration1

        # Many goals
        spec2 = Specification(
            spec_id="test2",
            title="Large",
            goals=[f"Goal {i}" for i in range(10)],
            non_goals=[],
            personas={},
            user_journeys=[],
            acceptance_criteria=[],
        )

        duration2 = agent._estimate_duration(spec2)
        assert "weeks" in duration2

    def test_assess_risks(self):
        """Test risk assessment."""
        agent = DSPyPlannerAgent()

        spec = Specification(
            spec_id="test",
            title="Test",
            goals=[f"Goal {i}" for i in range(6)],
            non_goals=[],
            personas={},
            user_journeys=[],
            acceptance_criteria=[],
            constraints=["Time constraint", "Budget constraint"],
        )

        risks = agent._assess_risks(spec)

        assert len(risks) > 0
        assert any(r["risk"] == "Scope creep" for r in risks)
        assert any(r["risk"] == "Constraint violations" for r in risks)


# ===========================
# Integration Tests
# ===========================


class TestIntegration:
    """Test integration scenarios."""

    def test_complete_planning_flow(self, tmp_path):
        """Test complete planning flow from request to tasks."""
        specs_dir = tmp_path / "specs"
        plans_dir = tmp_path / "plans"

        agent = DSPyPlannerAgent(specs_dir=str(specs_dir), plans_dir=str(plans_dir))

        result = agent.forward("Build a user authentication system with OAuth support", mode="full")

        assert result.success is True
        assert result.requirement_type.category == "feature"

        # For complex features, should have spec and plan
        if result.requirement_type.requires_spec:
            assert result.specification is not None
            assert result.technical_plan is not None
            assert len(result.tasks) > 0

    def test_simple_task_flow(self):
        """Test simple task flow without spec generation."""
        agent = DSPyPlannerAgent()

        result = agent.forward("Fix typo in README", mode="simple")

        assert result.success is True
        assert result.requirement_type.requires_spec is False
        assert result.guidance is not None
        assert result.specification is None
        assert result.technical_plan is None

    def test_context_preparation(self):
        """Test context preparation with all parameters."""
        agent = DSPyPlannerAgent()

        context = agent._prepare_context(
            "Test request",
            "full",
            codebase_context={"files": 100},
            learning_patterns=[{"pattern": "test"}],
        )

        assert context.request == "Test request"
        assert context.mode == "full"
        assert context.codebase_context["files"] == 100
        assert len(context.learning_patterns) == 1
        assert len(context.constitutional_requirements) == 5
