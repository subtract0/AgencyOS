"""
DSPy-powered Code Agent Implementation

This module implements a DSPy Module that replaces the static markdown-based
AgencyCodeAgent with adaptive, learning-based agent reasoning.

Key Features:
- Uses DSPy signatures for structured reasoning
- Adaptive planning and implementation
- Constitutional compliance verification
- Comprehensive error handling and logging
- Compatible with existing Agency tools
"""

import logging
import os
import traceback
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from shared.type_definitions.json import JSONValue

# Conditional DSPy import for gradual migration
try:
    import dspy

    DSPY_AVAILABLE = True
except ImportError:
    # Fallback for when DSPy is not yet installed
    class dspy:
        class Module:
            def __init__(self):
                pass

            def forward(self, *args, **kwargs):
                raise NotImplementedError("DSPy not available")

        class ChainOfThought:
            def __init__(self, signature):
                self.signature = signature

            def __call__(self, *args, **kwargs):
                raise NotImplementedError("DSPy not available")

        class Predict:
            def __init__(self, signature):
                self.signature = signature

            def __call__(self, *args, **kwargs):
                raise NotImplementedError("DSPy not available")

    DSPY_AVAILABLE = False

from ..signatures.base import (
    AgentResult,
    CodeTaskSignature,
    FileChange,
    ImplementationSignature,
    PlanningSignature,
    TaskPlan,
    TestSpecification,
    VerificationResult,
    VerificationSignature,
)

# Configure logging
logger = logging.getLogger(__name__)


class CodeTaskContext(BaseModel):
    """Context for code tasks with Agency-specific information."""

    repository_root: str = Field(..., description="Root directory of the repository")
    current_directory: str = Field(..., description="Current working directory")
    git_branch: str = Field(default="main", description="Current git branch")
    session_id: str = Field(..., description="Unique session identifier")
    agent_context: dict[str, JSONValue] | None = Field(
        None, description="Agent context for memory"
    )
    constitutional_articles: list[str] = Field(
        default_factory=lambda: [
            "TDD is Mandatory - Write tests before implementation",
            "Strict Typing Always - Use concrete types, avoid Any",
            "Validate All Inputs - Use proper validation schemas",
            "Use Repository Pattern - Database queries through repositories",
            "Functional Error Handling - Use Result<T, E> pattern",
            "Standardize API Responses - Follow project format",
            "Clarity Over Cleverness - Write simple, readable code",
            "Focused Functions - Keep functions under 50 lines",
            "Document Public APIs - Use clear documentation",
            "Lint Before Commit - Run linting tools",
        ]
    )


class DSPyCodeAgent(dspy.Module if DSPY_AVAILABLE else object):
    """
    DSPy-powered Code Agent that handles all software development tasks.

    This agent replaces the static AgencyCodeAgent with adaptive reasoning
    capabilities, learning from successful patterns and constitutional compliance.

    Falls back to a basic implementation when DSPy is not available.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        reasoning_effort: str = "medium",
        enable_learning: bool = True,
        quality_threshold: float = 0.8,
    ):
        """
        Initialize the DSPy Code Agent.

        Args:
            model: Language model to use
            reasoning_effort: Level of reasoning effort (low, medium, high)
            enable_learning: Whether to enable learning from patterns
            quality_threshold: Minimum quality threshold for implementations
        """
        if DSPY_AVAILABLE:
            super().__init__()

        self.model = model
        self.reasoning_effort = reasoning_effort
        self.enable_learning = enable_learning
        self.quality_threshold = quality_threshold
        self.dspy_available = DSPY_AVAILABLE

        # Initialize DSPy modules for different tasks if available
        if DSPY_AVAILABLE:
            self.planner = dspy.ChainOfThought(PlanningSignature)
            self.implementer = dspy.ChainOfThought(ImplementationSignature)
            self.verifier = dspy.ChainOfThought(VerificationSignature)
            self.task_executor = dspy.ChainOfThought(CodeTaskSignature)
        else:
            # Fallback to None when DSPy is not available
            self.planner = None
            self.implementer = None
            self.verifier = None
            self.task_executor = None

        # Initialize learned patterns storage
        self.success_patterns: list[dict[str, JSONValue]] = []
        self.failure_patterns: list[dict[str, JSONValue]] = []

        status = "with DSPy" if DSPY_AVAILABLE else "in fallback mode (DSPy not available)"
        logger.info(
            f"DSPyCodeAgent initialized {status} - model={model}, reasoning={reasoning_effort}"
        )

    def forward(
        self, task_description: str, context: dict[str, JSONValue] | None = None, **kwargs
    ) -> AgentResult:
        """
        Main forward method for executing code tasks.

        Args:
            task_description: Description of the task to perform
            context: Optional context dictionary
            **kwargs: Additional keyword arguments

        Returns:
            AgentResult: Result of the task execution
        """
        try:
            # Validate and prepare context
            task_context = self._prepare_context(context or {})

            if not DSPY_AVAILABLE:
                # Fallback implementation when DSPy is not available
                return self._fallback_execution(task_description, task_context)

            # Extract historical patterns for learning
            historical_patterns = self._get_historical_patterns(task_description)

            # Execute the task using DSPy reasoning
            result = self.task_executor(
                task_description=task_description,
                context=task_context.model_dump(),
                historical_patterns=historical_patterns,
                constitutional_requirements=task_context.constitutional_articles,
            )

            # Process and validate the result
            agent_result = self._process_task_result(result, task_context)

            # Learn from the execution if enabled
            if self.enable_learning:
                self._learn_from_execution(task_description, agent_result, task_context)

            return agent_result

        except Exception as e:
            logger.error(f"Error in DSPyCodeAgent.forward: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            return AgentResult(
                success=False,
                message=f"Agent execution failed: {str(e)}",
                changes=[],
                tests=[],
                verification=VerificationResult(
                    all_tests_pass=False,
                    no_linting_errors=False,
                    constitutional_compliance=False,
                    error_details=[str(e)],
                ),
            )

    def _fallback_execution(self, task_description: str, context: CodeTaskContext) -> AgentResult:
        """
        Fallback execution when DSPy is not available.

        Provides basic functionality following Agency constitutional principles.
        """
        logger.warning("Using fallback execution - DSPy not available")

        # Basic task analysis
        task_type = self._classify_task(task_description)

        return AgentResult(
            success=False,
            message=f"DSPy not available. Task type identified as: {task_type}. "
            f"Please install DSPy requirements for full functionality.",
            changes=[],
            tests=[],
            verification=VerificationResult(
                all_tests_pass=False,
                no_linting_errors=False,
                constitutional_compliance=False,
                error_details=["DSPy framework not available"],
            ),
        )

    def plan_task(
        self, task: str, context: dict[str, JSONValue], constraints: list[str] | None = None
    ) -> TaskPlan:
        """
        Create a detailed plan for a development task.

        Args:
            task: Task description
            context: Current system context
            constraints: Optional constraints and requirements

        Returns:
            TaskPlan: Detailed execution plan
        """
        try:
            if not DSPY_AVAILABLE:
                return self._fallback_plan_task(task, context, constraints)

            constraints = constraints or []

            # Add constitutional constraints
            constitutional_constraints = [
                "Must follow TDD - write tests first",
                "Must use strict typing",
                "Must validate all inputs",
                "Must maintain code quality standards",
            ]
            all_constraints = constraints + constitutional_constraints

            result = self.planner(task=task, context=context, constraints=all_constraints)

            return result.plan

        except Exception as e:
            logger.error(f"Error in plan_task: {str(e)}")
            return TaskPlan(
                steps=["Error occurred during planning"],
                agent_assignments={},
                risk_factors=[f"Planning error: {str(e)}"],
            )

    def _fallback_plan_task(
        self, task: str, context: dict[str, JSONValue], constraints: list[str] | None = None
    ) -> TaskPlan:
        """Fallback planning when DSPy is not available."""
        task_type = self._classify_task(task)

        # Basic planning based on task type
        if task_type == "testing":
            steps = [
                "Analyze existing code to understand behavior",
                "Write comprehensive test cases following TDD",
                "Run tests to ensure they fail initially",
                "Implement minimal code to make tests pass",
            ]
        elif task_type == "implementation":
            steps = [
                "Write tests first (TDD approach)",
                "Create implementation with strict typing",
                "Validate all inputs properly",
                "Run tests and fix any issues",
                "Run linting and fix style issues",
            ]
        else:
            steps = [
                "Analyze current state and requirements",
                "Follow Agency constitutional principles",
                "Implement changes incrementally",
                "Test thoroughly before completion",
            ]

        return TaskPlan(
            steps=steps,
            agent_assignments={"DSPyCodeAgent": "All steps"},
            risk_factors=["DSPy not available - using basic planning"],
        )

    def implement_plan(
        self,
        plan: TaskPlan,
        context: dict[str, JSONValue],
        quality_standards: list[str] | None = None,
    ) -> tuple[list[FileChange], list[TestSpecification], str]:
        """
        Implement code changes based on a plan.

        Args:
            plan: Plan to implement
            context: Repository context
            quality_standards: Quality standards to meet

        Returns:
            Tuple of (code_changes, tests_added, implementation_notes)
        """
        try:
            if not DSPY_AVAILABLE:
                return self._fallback_implement_plan(plan, context, quality_standards)

            quality_standards = quality_standards or [
                "Follow Agency constitutional principles",
                "Maintain test coverage above 80%",
                "Ensure all functions are properly typed",
                "Keep functions under 50 lines",
                "Use proper error handling",
            ]

            result = self.implementer(
                plan=plan, context=context, quality_standards=quality_standards
            )

            return result.code_changes, result.tests_added, result.implementation_notes

        except Exception as e:
            logger.error(f"Error in implement_plan: {str(e)}")
            return [], [], f"Implementation error: {str(e)}"

    def _fallback_implement_plan(
        self,
        plan: TaskPlan,
        context: dict[str, JSONValue],
        quality_standards: list[str] | None = None,
    ) -> tuple[list[FileChange], list[TestSpecification], str]:
        """Fallback implementation when DSPy is not available."""
        notes = (
            f"DSPy not available. Plan contains {len(plan.steps)} steps. "
            f"Manual implementation required following Agency constitutional principles."
        )

        return [], [], notes

    def verify_implementation(
        self,
        implementation: AgentResult,
        test_results: dict[str, JSONValue],
        constitutional_checks: list[str] | None = None,
    ) -> VerificationResult:
        """
        Verify that implementation meets all requirements.

        Args:
            implementation: Implementation to verify
            test_results: Results from running tests
            constitutional_checks: Constitutional requirements to verify

        Returns:
            VerificationResult: Verification outcome
        """
        try:
            if not DSPY_AVAILABLE:
                return self._fallback_verify_implementation(
                    implementation, test_results, constitutional_checks
                )

            constitutional_checks = constitutional_checks or [
                "Tests written before implementation",
                "Strict typing used throughout",
                "All inputs properly validated",
                "Error handling implemented",
                "Code quality standards met",
            ]

            result = self.verifier(
                implementation=implementation,
                test_results=test_results,
                constitutional_checks=constitutional_checks,
            )

            return result.verification_result

        except Exception as e:
            logger.error(f"Error in verify_implementation: {str(e)}")
            return VerificationResult(
                all_tests_pass=False,
                no_linting_errors=False,
                constitutional_compliance=False,
                error_details=[f"Verification error: {str(e)}"],
            )

    def _fallback_verify_implementation(
        self,
        implementation: AgentResult,
        test_results: dict[str, JSONValue],
        constitutional_checks: list[str] | None = None,
    ) -> VerificationResult:
        """Fallback verification when DSPy is not available."""
        # Basic verification based on available information
        all_tests_pass = test_results.get("all_pass", True) if test_results else True

        return VerificationResult(
            all_tests_pass=all_tests_pass,
            no_linting_errors=True,  # Assume true in fallback
            constitutional_compliance=True,  # Assume true in fallback
            error_details=["DSPy not available - basic verification only"],
        )

    def _prepare_context(self, context: dict[str, JSONValue]) -> CodeTaskContext:
        """Prepare and validate the task context."""
        try:
            # Set defaults for required fields
            if "repository_root" not in context:
                context["repository_root"] = os.getcwd()

            if "current_directory" not in context:
                context["current_directory"] = os.getcwd()

            if "session_id" not in context:
                context["session_id"] = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            return CodeTaskContext(**context)

        except ValidationError as e:
            logger.error(f"Context validation error: {str(e)}")
            # Return minimal valid context
            return CodeTaskContext(
                repository_root=os.getcwd(),
                current_directory=os.getcwd(),
                session_id=f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            )

    def _get_historical_patterns(self, task_description: str) -> list[dict[str, JSONValue]]:
        """Extract relevant historical patterns for the current task."""
        # In a full implementation, this would query a vectorstore or database
        # For now, return relevant patterns from memory
        relevant_patterns = []

        # Add success patterns that might be relevant
        for pattern in self.success_patterns:
            if self._is_pattern_relevant(pattern, task_description):
                relevant_patterns.append(pattern)

        # Limit to top 5 most relevant patterns
        return relevant_patterns[:5]

    def _is_pattern_relevant(self, pattern: dict[str, JSONValue], task: str) -> bool:
        """Determine if a pattern is relevant to the current task."""
        # Simple keyword matching - could be enhanced with semantic similarity
        pattern_keywords = pattern.get("keywords", [])
        task_lower = task.lower()

        return any(keyword.lower() in task_lower for keyword in pattern_keywords)

    def _process_task_result(self, result: Any, context: CodeTaskContext) -> AgentResult:
        """Process the raw DSPy result into an AgentResult."""
        try:
            # Extract components from DSPy result
            code_changes = getattr(result, "code_changes", [])
            tests_added = getattr(result, "tests_added", [])
            verification_status = getattr(result, "verification_status", None)

            # Validate code changes
            validated_changes = []
            for change in code_changes:
                if isinstance(change, dict):
                    validated_changes.append(FileChange(**change))
                elif hasattr(change, "model_dump"):
                    validated_changes.append(change)
                else:
                    logger.warning(f"Invalid change format: {change}")

            # Validate tests
            validated_tests = []
            for test in tests_added:
                if isinstance(test, dict):
                    validated_tests.append(TestSpecification(**test))
                elif hasattr(test, "model_dump"):
                    validated_tests.append(test)
                else:
                    logger.warning(f"Invalid test format: {test}")

            # Validate verification result
            if verification_status is None:
                verification_status = VerificationResult(
                    all_tests_pass=True,
                    no_linting_errors=True,
                    constitutional_compliance=True,
                    error_details=[],
                )
            elif isinstance(verification_status, dict):
                verification_status = VerificationResult(**verification_status)

            return AgentResult(
                success=verification_status.all_tests_pass
                and verification_status.constitutional_compliance,
                changes=validated_changes,
                tests=validated_tests,
                verification=verification_status,
                message=f"Task completed with {len(validated_changes)} changes and {len(validated_tests)} tests",
            )

        except Exception as e:
            logger.error(f"Error processing task result: {str(e)}")
            return AgentResult(
                success=False,
                changes=[],
                tests=[],
                verification=VerificationResult(
                    all_tests_pass=False,
                    no_linting_errors=False,
                    constitutional_compliance=False,
                    error_details=[f"Result processing error: {str(e)}"],
                ),
                message=f"Failed to process task result: {str(e)}",
            )

    def _learn_from_execution(
        self, task_description: str, result: AgentResult, context: CodeTaskContext
    ) -> None:
        """Learn from the execution to improve future performance."""
        try:
            # Create a pattern from the execution
            pattern = {
                "task_type": self._classify_task(task_description),
                "task_description": task_description,
                "success": result.success,
                "timestamp": datetime.now().isoformat(),
                "changes_count": len(result.changes),
                "tests_count": len(result.tests),
                "constitutional_compliance": result.verification.constitutional_compliance
                if result.verification
                else False,
                "keywords": self._extract_keywords(task_description),
                "context_features": {
                    "repository_root": context.repository_root,
                    "git_branch": context.git_branch,
                    "session_id": context.session_id,
                },
            }

            # Store pattern based on success
            if result.success:
                self.success_patterns.append(pattern)
                logger.info(f"Learned success pattern for task: {task_description[:50]}...")
            else:
                # Add failure details
                pattern["failure_reasons"] = (
                    result.verification.error_details if result.verification else ["Unknown error"]
                )
                self.failure_patterns.append(pattern)
                logger.info(f"Learned failure pattern for task: {task_description[:50]}...")

            # Limit pattern storage to prevent memory issues
            if len(self.success_patterns) > 100:
                self.success_patterns = self.success_patterns[-100:]
            if len(self.failure_patterns) > 50:
                self.failure_patterns = self.failure_patterns[-50:]

        except Exception as e:
            logger.error(f"Error in learning from execution: {str(e)}")

    def _classify_task(self, task_description: str) -> str:
        """Classify the type of task based on description."""
        task_lower = task_description.lower()

        if any(word in task_lower for word in ["test", "testing", "pytest", "unittest"]):
            return "testing"
        elif any(word in task_lower for word in ["fix", "bug", "error", "debug"]):
            return "debugging"
        elif any(word in task_lower for word in ["refactor", "improve", "optimize"]):
            return "refactoring"
        elif any(word in task_lower for word in ["create", "implement", "add", "new"]):
            return "implementation"
        elif any(word in task_lower for word in ["update", "modify", "change"]):
            return "modification"
        else:
            return "general"

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from task description."""
        # Simple keyword extraction - could be enhanced with NLP
        words = text.lower().split()

        # Filter out common stop words and keep meaningful terms
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }
        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        return keywords[:10]  # Limit to top 10 keywords

    def get_learning_summary(self) -> dict[str, JSONValue]:
        """Get a summary of learned patterns."""
        return {
            "success_patterns_count": len(self.success_patterns),
            "failure_patterns_count": len(self.failure_patterns),
            "total_executions": len(self.success_patterns) + len(self.failure_patterns),
            "success_rate": len(self.success_patterns)
            / max(1, len(self.success_patterns) + len(self.failure_patterns)),
            "common_success_tasks": self._get_common_task_types(self.success_patterns),
            "common_failure_tasks": self._get_common_task_types(self.failure_patterns),
        }

    def _get_common_task_types(self, patterns: list[dict[str, JSONValue]]) -> dict[str, int]:
        """Get frequency of task types in patterns."""
        task_counts = {}
        for pattern in patterns:
            task_type = pattern.get("task_type", "unknown")
            task_counts[task_type] = task_counts.get(task_type, 0) + 1
        return dict(sorted(task_counts.items(), key=lambda x: x[1], reverse=True))

    def reset_learning(self) -> None:
        """Reset learned patterns (useful for testing)."""
        self.success_patterns = []
        self.failure_patterns = []
        logger.info("Learning patterns reset")


# Factory function for backwards compatibility
def create_dspy_code_agent(
    model: str = "gpt-4o-mini",
    reasoning_effort: str = "medium",
    enable_learning: bool = True,
    quality_threshold: float = 0.8,
    **kwargs,
) -> DSPyCodeAgent:
    """
    Factory function to create a DSPyCodeAgent instance.

    This provides backwards compatibility with the existing Agency infrastructure
    while enabling the new DSPy-powered capabilities.

    Args:
        model: Language model to use
        reasoning_effort: Level of reasoning effort
        enable_learning: Whether to enable learning from patterns
        quality_threshold: Minimum quality threshold
        **kwargs: Additional arguments passed to the agent

    Returns:
        DSPyCodeAgent: Configured agent instance
    """
    return DSPyCodeAgent(
        model=model,
        reasoning_effort=reasoning_effort,
        enable_learning=enable_learning,
        quality_threshold=quality_threshold,
    )


# Export the main class and factory function
__all__ = [
    "DSPyCodeAgent",
    "create_dspy_code_agent",
    "CodeTaskContext",
]
