"""
DSPy PlannerAgent Module

Implements strategic planning and task orchestration using DSPy,
following the spec-kit methodology and constitutional requirements.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from shared.type_definitions.json import JSONValue

# Conditional DSPy import with fallback
try:
    import dspy

    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False

    # Provide fallback implementations
    class dspy:
        class Module:
            pass

        class ChainOfThought:
            def __init__(self, signature):
                self.signature = signature

            def __call__(self, **kwargs):
                return type("Result", (), kwargs)()

        class Predict:
            def __init__(self, signature):
                self.signature = signature

            def __call__(self, **kwargs):
                return type("Result", (), kwargs)()


from dspy_agents.signatures.base import (
    StrategySignature,
    TaskBreakdownSignature,
    UnderstandingSignature,
)

logger = logging.getLogger(__name__)


# ===========================
# Data Models
# ===========================


class RequirementType(BaseModel):
    """Type of requirement for classification."""

    model_config = ConfigDict(extra="forbid")

    category: str = Field(..., description="Category: feature, bugfix, refactor, docs, test")
    complexity: str = Field(..., description="Complexity: simple, moderate, complex")
    requires_spec: bool = Field(..., description="Whether spec-kit process is needed")
    estimated_effort: str = Field(..., description="Effort estimate: hours, days, weeks")


class Specification(BaseModel):
    """Formal specification following spec-kit methodology."""

    model_config = ConfigDict(extra="forbid")

    spec_id: str = Field(..., description="Unique specification ID")
    title: str = Field(..., description="Clear, descriptive title")
    goals: list[str] = Field(..., description="Specific, measurable objectives")
    non_goals: list[str] = Field(..., description="Explicit scope boundaries")
    personas: dict[str, str] = Field(..., description="User personas and their needs")
    user_journeys: list[dict[str, JSONValue]] = Field(..., description="Detailed use cases")
    acceptance_criteria: list[str] = Field(..., description="Testable success conditions")
    constraints: list[str] = Field(
        default_factory=list, description="Technical or business constraints"
    )
    assumptions: list[str] = Field(default_factory=list, description="Planning assumptions")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field("draft", description="Status: draft, approved, implemented")


class TechnicalPlan(BaseModel):
    """Technical implementation plan."""

    model_config = ConfigDict(extra="forbid")

    plan_id: str = Field(..., description="Unique plan ID")
    spec_id: str = Field(..., description="Reference to specification")
    architecture: dict[str, JSONValue] = Field(..., description="System design and components")
    agent_assignments: dict[str, list[str]] = Field(..., description="Agent to task mapping")
    tool_requirements: list[str] = Field(..., description="Required tools")
    contracts: dict[str, JSONValue] = Field(..., description="APIs and interfaces")
    quality_strategy: dict[str, JSONValue] = Field(
        ..., description="Testing and validation approach"
    )
    risk_assessment: list[dict[str, JSONValue]] = Field(..., description="Risks and mitigations")
    milestones: list[dict[str, JSONValue]] = Field(..., description="Key milestones")
    estimated_duration: str = Field(..., description="Total estimated time")
    dependencies: list[str] = Field(default_factory=list, description="External dependencies")


class PlanningContext(BaseModel):
    """Context for planning operations."""

    model_config = ConfigDict(extra="forbid")

    request: str = Field(..., description="User request or requirement")
    mode: str = Field("full", description="Planning mode: full, simple, guidance")
    existing_specs: list[str] = Field(default_factory=list, description="Existing specifications")
    existing_plans: list[str] = Field(default_factory=list, description="Existing plans")
    codebase_context: dict[str, JSONValue] = Field(
        default_factory=dict, description="Current codebase state"
    )
    constitutional_requirements: list[str] = Field(
        default_factory=list, description="Constitution articles to follow"
    )
    learning_patterns: list[dict[str, JSONValue]] = Field(
        default_factory=list, description="Relevant historical patterns"
    )


class PlanningResult(BaseModel):
    """Complete planning result."""

    model_config = ConfigDict(extra="forbid")

    success: bool = Field(..., description="Whether planning succeeded")
    requirement_type: RequirementType = Field(..., description="Classified requirement")
    specification: Specification | None = Field(
        None, description="Generated specification if needed"
    )
    technical_plan: TechnicalPlan | None = Field(None, description="Generated technical plan")
    tasks: list[dict[str, JSONValue]] = Field(default_factory=list, description="Task breakdown")
    guidance: str | None = Field(None, description="Direct guidance for simple tasks")
    recommendations: list[str] = Field(default_factory=list, description="Planning recommendations")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ===========================
# DSPy Planner Agent
# ===========================


class DSPyPlannerAgent(dspy.Module if DSPY_AVAILABLE else object):
    """
    DSPy-based Planner Agent for strategic planning and task orchestration.

    This agent specializes in:
    - Spec-kit methodology implementation
    - Formal specification generation
    - Technical planning and architecture
    - Task breakdown and orchestration
    - Constitutional compliance in planning
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        reasoning_effort: str = "high",
        enable_learning: bool = True,
        specs_dir: str = "specs",
        plans_dir: str = "plans",
    ):
        """
        Initialize the DSPy Planner Agent.

        Args:
            model: Model to use for reasoning
            reasoning_effort: Level of reasoning effort
            enable_learning: Whether to enable learning from planning
            specs_dir: Directory for specifications
            plans_dir: Directory for technical plans
        """
        if DSPY_AVAILABLE:
            super().__init__()

        self.model = model
        self.reasoning_effort = reasoning_effort
        self.enable_learning = enable_learning
        self.specs_dir = Path(specs_dir)
        self.plans_dir = Path(plans_dir)

        # Create directories if they don't exist
        self.specs_dir.mkdir(exist_ok=True)
        self.plans_dir.mkdir(exist_ok=True)

        # Initialize DSPy components
        if DSPY_AVAILABLE:
            self.understand = dspy.ChainOfThought(UnderstandingSignature)
            self.strategize = dspy.ChainOfThought(StrategySignature)
            self.breakdown = dspy.Predict(TaskBreakdownSignature)
        else:
            # Fallback implementations
            self.understand = self._fallback_understand
            self.strategize = self._fallback_strategize
            self.breakdown = self._fallback_breakdown

        # Planning history for learning
        self.planning_history: list[dict[str, JSONValue]] = []

        logger.info(
            f"DSPyPlannerAgent initialized with model={model}, DSPy available: {DSPY_AVAILABLE}"
        )

    def forward(self, request: str, mode: str = "full", **kwargs) -> PlanningResult:
        """
        Main execution method for the planner.

        Args:
            request: User request or requirement
            mode: Planning mode (full, simple, guidance)
            **kwargs: Additional context

        Returns:
            Complete planning result
        """
        # Prepare context
        context = self._prepare_context(request, mode, **kwargs)

        # Phase 1: Understand and classify requirement
        requirement_type = self._classify_requirement(context)

        # Phase 2: Determine planning approach
        if not requirement_type.requires_spec:
            # Simple task - provide direct guidance
            guidance = self._generate_guidance(context, requirement_type)
            result = PlanningResult(
                success=True,
                requirement_type=requirement_type,
                guidance=guidance,
                recommendations=["Simple task - no formal specification needed"],
            )
        else:
            # Complex task - follow spec-kit process
            result = self._execute_spec_kit_process(context, requirement_type)

        # Learn from this planning session
        if self.enable_learning:
            self._learn_from_planning(result)

        return result

    def _prepare_context(self, request: str, mode: str, **kwargs) -> PlanningContext:
        """Prepare planning context from inputs."""
        # Load existing specs and plans
        existing_specs = self._list_existing_specs()
        existing_plans = self._list_existing_plans()

        # Get constitutional requirements
        constitutional_requirements = [
            "Article I: Complete Context Before Action",
            "Article II: 100% Verification and Stability",
            "Article III: Automated Merge Enforcement",
            "Article IV: Continuous Learning and Improvement",
            "Article V: Spec-Driven Development",
        ]

        return PlanningContext(
            request=request,
            mode=mode,
            existing_specs=existing_specs,
            existing_plans=existing_plans,
            codebase_context=kwargs.get("codebase_context", {}),
            constitutional_requirements=constitutional_requirements,
            learning_patterns=kwargs.get("learning_patterns", []),
        )

    def _classify_requirement(self, context: PlanningContext) -> RequirementType:
        """Classify the requirement type and complexity."""
        # Analyze request to determine type and complexity
        request_lower = context.request.lower()

        # Determine category (check test first as it's more specific)
        if any(
            word in request_lower for word in ["test", "tests", "testing", "coverage", "unit test"]
        ):
            category = "test"
        elif any(word in request_lower for word in ["bug", "fix", "issue", "error"]):
            category = "bugfix"
        elif any(word in request_lower for word in ["refactor", "improve", "optimize"]):
            category = "refactor"
        elif any(word in request_lower for word in ["document", "docs", "readme"]):
            category = "docs"
        elif any(word in request_lower for word in ["feature", "add", "implement", "create"]):
            category = "feature"
        else:
            category = "feature"

        # Determine complexity
        # Simple: Single file changes, clear scope
        # Moderate: Multiple files, some design needed
        # Complex: Architecture changes, multiple agents, new systems
        word_count = len(context.request.split())

        if word_count < 20 and category in ["bugfix", "docs"]:
            complexity = "simple"
            requires_spec = False
            estimated_effort = "hours"
        elif word_count < 50 and category != "feature":
            complexity = "moderate"
            requires_spec = category == "feature"
            estimated_effort = "days"
        else:
            complexity = "complex"
            requires_spec = True
            estimated_effort = "weeks"

        return RequirementType(
            category=category,
            complexity=complexity,
            requires_spec=requires_spec,
            estimated_effort=estimated_effort,
        )

    def _generate_guidance(
        self, context: PlanningContext, requirement_type: RequirementType
    ) -> str:
        """Generate direct guidance for simple tasks."""
        guidance_parts = []

        # Add header
        guidance_parts.append(f"## Direct Guidance for {requirement_type.category.title()}")
        guidance_parts.append(f"**Complexity**: {requirement_type.complexity}")
        guidance_parts.append(f"**Estimated Effort**: {requirement_type.estimated_effort}\n")

        # Add specific guidance based on category
        if requirement_type.category == "bugfix":
            guidance_parts.append("### Steps to Fix:")
            guidance_parts.append("1. Locate the error in the codebase")
            guidance_parts.append("2. Analyze root cause")
            guidance_parts.append("3. Implement fix with tests")
            guidance_parts.append("4. Verify all tests pass")
        elif requirement_type.category == "docs":
            guidance_parts.append("### Documentation Steps:")
            guidance_parts.append("1. Identify what needs documenting")
            guidance_parts.append("2. Create or update relevant files")
            guidance_parts.append("3. Ensure clarity and completeness")
            guidance_parts.append("4. Add examples where helpful")
        elif requirement_type.category == "test":
            guidance_parts.append("### Testing Steps:")
            guidance_parts.append("1. Identify untested functionality")
            guidance_parts.append("2. Write comprehensive test cases")
            guidance_parts.append("3. Follow NECESSARY pattern")
            guidance_parts.append("4. Ensure 100% pass rate")
        else:
            guidance_parts.append("### Implementation Steps:")
            guidance_parts.append("1. Understand requirements fully")
            guidance_parts.append("2. Plan implementation approach")
            guidance_parts.append("3. Write code with tests")
            guidance_parts.append("4. Verify and document")

        # Add constitutional reminder
        guidance_parts.append("\n### Constitutional Compliance:")
        guidance_parts.append("- Ensure complete context (Article I)")
        guidance_parts.append("- Maintain 100% test success (Article II)")
        guidance_parts.append("- Follow quality gates (Article III)")

        return "\n".join(guidance_parts)

    def _execute_spec_kit_process(
        self, context: PlanningContext, requirement_type: RequirementType
    ) -> PlanningResult:
        """Execute full spec-kit process for complex tasks."""
        try:
            # Step 1: Generate specification
            specification = self._generate_specification(context, requirement_type)

            # Step 2: Generate technical plan
            technical_plan = self._generate_technical_plan(context, specification)

            # Step 3: Break down into tasks
            tasks = self._generate_task_breakdown(technical_plan, specification)

            # Step 4: Generate recommendations
            recommendations = self._generate_recommendations(specification, technical_plan)

            return PlanningResult(
                success=True,
                requirement_type=requirement_type,
                specification=specification,
                technical_plan=technical_plan,
                tasks=tasks,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Spec-kit process failed: {e}")
            return PlanningResult(
                success=False,
                requirement_type=requirement_type,
                recommendations=[f"Planning failed: {str(e)}"],
            )

    def _generate_specification(
        self, context: PlanningContext, requirement_type: RequirementType
    ) -> Specification:
        """Generate formal specification."""
        # Generate unique spec ID
        spec_id = f"spec-{len(context.existing_specs) + 1:03d}-{requirement_type.category}"

        # Use DSPy or fallback to understand requirements
        if DSPY_AVAILABLE and hasattr(self.understand, "__call__"):
            try:
                result = self.understand(
                    request=context.request,
                    existing_context=context.codebase_context,
                    clarifying_questions=[],
                )

                understanding = result.understanding
                assumptions = result.assumptions
                risks = result.risks
            except Exception as e:
                logger.warning(f"DSPy understanding failed: {e}, using fallback")
                understanding = context.request
                assumptions = ["Requirements are clear and complete"]
                risks = ["Requirements may need clarification"]
        else:
            understanding = context.request
            assumptions = ["Requirements are clear and complete"]
            risks = ["Requirements may need clarification"]

        # Extract goals from understanding
        goals = self._extract_goals(understanding)

        # Define non-goals
        non_goals = self._define_non_goals(requirement_type)

        # Create personas
        personas = self._create_personas(requirement_type)

        # Define user journeys
        user_journeys = self._create_user_journeys(requirement_type, personas)

        # Generate acceptance criteria
        acceptance_criteria = self._generate_acceptance_criteria(goals)

        return Specification(
            spec_id=spec_id,
            title=f"{requirement_type.category.title()} Implementation",
            goals=goals,
            non_goals=non_goals,
            personas=personas,
            user_journeys=user_journeys,
            acceptance_criteria=acceptance_criteria,
            constraints=risks,
            assumptions=assumptions,
        )

    def _generate_technical_plan(
        self, context: PlanningContext, specification: Specification
    ) -> TechnicalPlan:
        """Generate technical implementation plan."""
        # Generate unique plan ID
        plan_id = f"plan-{specification.spec_id}"

        # Use DSPy or fallback to create strategy
        if DSPY_AVAILABLE and hasattr(self.strategize, "__call__"):
            try:
                result = self.strategize(
                    understanding="\n".join(specification.goals),
                    constraints=specification.constraints,
                    available_resources={"agents": ["code", "auditor", "test_generator"]},
                )

                strategy = result.strategy
                milestones = [{"name": m, "description": m} for m in result.milestones]
                success_criteria = result.success_criteria
            except Exception as e:
                logger.warning(f"DSPy strategy failed: {e}, using fallback")
                strategy = "Implement features according to specification"
                milestones = [
                    {"name": "Implementation Complete", "description": "All features implemented"}
                ]
                success_criteria = specification.acceptance_criteria
        else:
            strategy = "Implement features according to specification"
            milestones = [
                {"name": "Implementation Complete", "description": "All features implemented"}
            ]
            success_criteria = specification.acceptance_criteria

        # Design architecture
        architecture = {
            "overview": strategy,
            "components": self._identify_components(specification),
            "data_flow": "Request -> Processing -> Response",
            "integration_points": [],
        }

        # Assign agents
        agent_assignments = self._assign_agents(specification)

        # Identify tools
        tool_requirements = self._identify_tools(specification)

        # Define contracts
        contracts = {"interfaces": [], "apis": [], "data_models": []}

        # Create quality strategy
        quality_strategy = {
            "testing_approach": "TDD with NECESSARY pattern",
            "coverage_target": "100%",
            "validation_steps": success_criteria,
        }

        # Assess risks
        risk_assessment = self._assess_risks(specification)

        return TechnicalPlan(
            plan_id=plan_id,
            spec_id=specification.spec_id,
            architecture=architecture,
            agent_assignments=agent_assignments,
            tool_requirements=tool_requirements,
            contracts=contracts,
            quality_strategy=quality_strategy,
            risk_assessment=risk_assessment,
            milestones=milestones,
            estimated_duration=self._estimate_duration(specification),
            dependencies=[],
        )

    def _generate_task_breakdown(
        self, technical_plan: TechnicalPlan, specification: Specification
    ) -> list[dict[str, JSONValue]]:
        """Break down plan into executable tasks."""
        tasks = []

        # Use DSPy or fallback for task breakdown
        if DSPY_AVAILABLE and hasattr(self.breakdown, "__call__"):
            try:
                result = self.breakdown(
                    strategy=technical_plan.architecture["overview"],
                    agent_capabilities=technical_plan.agent_assignments,
                    dependencies=[],
                )

                if hasattr(result, "tasks"):
                    tasks = result.tasks
            except Exception as e:
                logger.warning(f"DSPy breakdown failed: {e}, using fallback")

        # Fallback or enhancement of tasks
        if not tasks:
            # Create tasks for each acceptance criterion
            for idx, criterion in enumerate(specification.acceptance_criteria):
                tasks.append(
                    {
                        "task_id": f"{technical_plan.plan_id}-task-{idx + 1}",
                        "title": f"Implement: {criterion[:50]}...",
                        "description": criterion,
                        "assigned_to": list(technical_plan.agent_assignments.keys())[0]
                        if technical_plan.agent_assignments
                        else "code",
                        "dependencies": [f"{technical_plan.plan_id}-task-{idx}"] if idx > 0 else [],
                        "estimated_hours": 4,
                        "status": "pending",
                    }
                )

        return tasks

    def _generate_recommendations(
        self, specification: Specification, technical_plan: TechnicalPlan
    ) -> list[str]:
        """Generate planning recommendations."""
        recommendations = []

        # Check specification completeness
        if len(specification.goals) < 3:
            recommendations.append("Consider adding more specific goals to the specification")

        if not specification.personas:
            recommendations.append("Define user personas for better user-centered design")

        # Check technical plan
        if len(technical_plan.agent_assignments) == 1:
            recommendations.append("Consider involving multiple agents for complex tasks")

        if not technical_plan.risk_assessment:
            recommendations.append("Add risk assessment to identify potential issues early")

        # Constitutional recommendations
        recommendations.append("Ensure complete context before starting (Article I)")
        recommendations.append("Plan for 100% test coverage (Article II)")
        recommendations.append("Follow spec-driven development process (Article V)")

        return recommendations

    # ===========================
    # Helper Methods
    # ===========================

    def _list_existing_specs(self) -> list[str]:
        """List existing specifications."""
        if self.specs_dir.exists():
            return [f.name for f in self.specs_dir.glob("spec-*.md")]
        return []

    def _list_existing_plans(self) -> list[str]:
        """List existing plans."""
        if self.plans_dir.exists():
            return [f.name for f in self.plans_dir.glob("plan-*.md")]
        return []

    def _extract_goals(self, understanding: str) -> list[str]:
        """Extract goals from understanding."""
        # Simple extraction - in practice, use NLP
        goals = []

        # Default goals based on understanding
        if "implement" in understanding.lower():
            goals.append("Implement the requested functionality")
        if "test" in understanding.lower():
            goals.append("Ensure comprehensive test coverage")
        if "document" in understanding.lower():
            goals.append("Provide clear documentation")

        if not goals:
            goals.append("Complete the requested task successfully")
            goals.append("Maintain code quality and standards")
            goals.append("Ensure constitutional compliance")

        return goals

    def _define_non_goals(self, requirement_type: RequirementType) -> list[str]:
        """Define what's out of scope."""
        non_goals = []

        if requirement_type.category == "feature":
            non_goals.append("Refactoring unrelated code")
            non_goals.append("Adding unrelated features")
        elif requirement_type.category == "bugfix":
            non_goals.append("Adding new features")
            non_goals.append("Major refactoring")
        elif requirement_type.category == "refactor":
            non_goals.append("Changing functionality")
            non_goals.append("Adding new features")

        return non_goals

    def _create_personas(self, requirement_type: RequirementType) -> dict[str, str]:
        """Create user personas."""
        personas = {
            "developer": "Software developer using the system",
            "end_user": "Final user of the application",
        }

        if requirement_type.category == "test":
            personas["qa_engineer"] = "Quality assurance engineer validating functionality"

        return personas

    def _create_user_journeys(
        self, requirement_type: RequirementType, personas: dict[str, str]
    ) -> list[dict[str, JSONValue]]:
        """Create user journey maps."""
        journeys = []

        for persona_id, persona_desc in personas.items():
            journeys.append(
                {
                    "persona": persona_id,
                    "description": persona_desc,
                    "steps": ["Initiate the action", "Perform the main task", "Verify the outcome"],
                    "expected_outcome": "Task completed successfully",
                }
            )

        return journeys

    def _generate_acceptance_criteria(self, goals: list[str]) -> list[str]:
        """Generate testable acceptance criteria."""
        criteria = []

        for goal in goals:
            # Create testable criterion for each goal
            criteria.append(
                f"GIVEN the system is ready WHEN {goal.lower()} THEN it completes successfully"
            )

        # Add standard criteria
        criteria.append("All tests pass with 100% success rate")
        criteria.append("Code follows established patterns and standards")
        criteria.append("Documentation is complete and accurate")

        return criteria

    def _identify_components(self, specification: Specification) -> list[dict[str, str]]:
        """Identify system components needed."""
        components = []

        # Basic components based on goals
        for goal in specification.goals:
            components.append(
                {
                    "name": f"Component for: {goal[:30]}...",
                    "responsibility": goal,
                    "type": "implementation",
                }
            )

        return components

    def _assign_agents(self, specification: Specification) -> dict[str, list[str]]:
        """Assign agents to tasks."""
        assignments = {
            "code": ["Implementation", "Integration"],
            "auditor": ["Quality assurance", "Compliance checking"],
            "test_generator": ["Test creation", "Coverage validation"],
        }

        return assignments

    def _identify_tools(self, specification: Specification) -> list[str]:
        """Identify required tools."""
        tools = ["Read", "Write", "Edit", "Grep", "Glob"]

        # Add specific tools based on needs
        for goal in specification.goals:
            if "test" in goal.lower():
                tools.append("pytest")
            if "document" in goal.lower():
                tools.append("markdown")

        return list(set(tools))

    def _assess_risks(self, specification: Specification) -> list[dict[str, JSONValue]]:
        """Assess project risks."""
        risks = []

        if len(specification.goals) > 5:
            risks.append(
                {
                    "risk": "Scope creep",
                    "impact": "high",
                    "mitigation": "Strict adherence to specification",
                }
            )

        if specification.constraints:
            risks.append(
                {
                    "risk": "Constraint violations",
                    "impact": "medium",
                    "mitigation": "Regular constraint validation",
                }
            )

        return risks

    def _estimate_duration(self, specification: Specification) -> str:
        """Estimate project duration."""
        # Simple heuristic based on goals
        num_goals = len(specification.goals)

        if num_goals <= 2:
            return "1-2 days"
        elif num_goals <= 5:
            return "3-5 days"
        else:
            return "1-2 weeks"

    def _learn_from_planning(self, result: PlanningResult) -> None:
        """Learn patterns from planning results."""
        learning_entry = {
            "timestamp": result.timestamp,
            "category": result.requirement_type.category,
            "complexity": result.requirement_type.complexity,
            "success": result.success,
            "had_spec": result.specification is not None,
            "num_tasks": len(result.tasks),
            "estimated_effort": result.requirement_type.estimated_effort,
        }

        self.planning_history.append(learning_entry)

        # Limit history size
        if len(self.planning_history) > 100:
            self.planning_history = self.planning_history[-100:]

        logger.info(
            f"Learned from planning: category={result.requirement_type.category}, success={result.success}"
        )

    # ===========================
    # Fallback Methods
    # ===========================

    def _fallback_understand(self, **kwargs) -> Any:
        """Fallback understanding when DSPy is not available."""
        logger.info("Using fallback understanding (DSPy not available)")
        return type(
            "Result",
            (),
            {
                "understanding": kwargs.get("request", ""),
                "assumptions": ["Requirements understood"],
                "risks": ["May need clarification"],
            },
        )()

    def _fallback_strategize(self, **kwargs) -> Any:
        """Fallback strategy when DSPy is not available."""
        return type(
            "Result",
            (),
            {
                "strategy": "Implement according to requirements",
                "milestones": ["Planning", "Implementation", "Testing"],
                "success_criteria": ["All requirements met"],
            },
        )()

    def _fallback_breakdown(self, **kwargs) -> Any:
        """Fallback task breakdown when DSPy is not available."""
        return type(
            "Result", (), {"tasks": [], "task_dependencies": {}, "estimated_duration": 100}
        )()

    def get_planning_summary(self) -> dict[str, JSONValue]:
        """Get summary of planning history."""
        if not self.planning_history:
            return {"message": "No planning sessions yet"}

        # Calculate statistics
        total_sessions = len(self.planning_history)
        successful = sum(1 for h in self.planning_history if h["success"])

        category_counts = {}
        for h in self.planning_history:
            cat = h["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "total_sessions": total_sessions,
            "success_rate": successful / total_sessions if total_sessions > 0 else 0,
            "category_distribution": category_counts,
            "average_tasks": sum(h["num_tasks"] for h in self.planning_history) / total_sessions
            if total_sessions > 0
            else 0,
            "recent_trend": self._calculate_planning_trend(),
        }

    def _calculate_planning_trend(self) -> str:
        """Calculate trend in planning success."""
        if len(self.planning_history) < 5:
            return "insufficient_data"

        recent = self.planning_history[-5:]
        recent_success = sum(1 for h in recent if h["success"]) / len(recent)

        older = (
            self.planning_history[-10:-5]
            if len(self.planning_history) >= 10
            else self.planning_history[: len(self.planning_history) // 2]
        )
        if not older:
            return "insufficient_data"

        older_success = sum(1 for h in older if h["success"]) / len(older)

        if recent_success > older_success:
            return "improving"
        elif recent_success < older_success:
            return "declining"
        else:
            return "stable"


# ===========================
# Factory Function
# ===========================


def create_dspy_planner_agent(
    model: str = "gpt-4o-mini",
    reasoning_effort: str = "high",
    enable_learning: bool = True,
    **kwargs,
) -> DSPyPlannerAgent:
    """
    Factory function to create a DSPy Planner Agent.

    Args:
        model: Model to use
        reasoning_effort: Reasoning effort level
        enable_learning: Whether to enable learning
        **kwargs: Additional configuration

    Returns:
        Configured DSPyPlannerAgent instance
    """
    return DSPyPlannerAgent(
        model=model, reasoning_effort=reasoning_effort, enable_learning=enable_learning, **kwargs
    )
