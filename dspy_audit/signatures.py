"""
DSPy Signatures for Audit and Refactoring

Defines typed input/output specifications for the audit system.
"""

from dataclasses import dataclass
from enum import Enum

# Note: DSPy will be imported conditionally to allow gradual migration
try:
    import dspy
except ImportError:
    # Fallback for when DSPy is not yet installed
    class DummySignature:
        pass

    class DummyField:
        def __init__(self, *args, **kwargs):
            pass

    class dspy:
        Signature = DummySignature
        InputField = DummyField
        OutputField = DummyField


class IssueSeverity(Enum):
    """Priority levels for identified issues."""

    CONSTITUTIONAL = "constitutional"  # P0 - Article violations
    SECURITY = "security"  # P1 - Security vulnerabilities
    QUALITY = "quality"  # P2 - Q(T) < 0.6
    COVERAGE = "coverage"  # P2 - Test coverage issues
    COMPLEXITY = "complexity"  # P3 - Complexity violations
    STYLE = "style"  # P3 - Style issues


@dataclass
class Issue:
    """Represents a single identified issue in the codebase."""

    file_path: str
    line_number: int
    severity: IssueSeverity
    category: str  # NECESSARY property or violation type
    description: str
    suggested_fix: str | None = None
    qt_impact: float = 0.0  # Impact on Q(T) score
    constitutional_article: int | None = None


@dataclass
class RefactoringStep:
    """A single step in a refactoring plan."""

    action: str  # "edit", "create", "delete", "move"
    target: str  # File or module to modify
    changes: dict[str, str]  # Old -> New mappings
    rationale: str
    estimated_risk: float  # 0.0 to 1.0


@dataclass
class RefactoringPlan:
    """Complete plan for fixing identified issues."""

    issue_id: str
    steps: list[RefactoringStep]
    test_requirements: list[str]
    rollback_strategy: str
    estimated_time: int  # minutes
    success_probability: float


class AuditSignature(dspy.Signature):
    """Analyze code for quality issues and constitutional violations."""

    # Inputs
    code_path: str = dspy.InputField(
        desc="Path to the code file or directory to analyze"
    )
    constitution_rules: list[str] = dspy.InputField(
        desc="List of constitutional articles and requirements"
    )
    historical_patterns: list[dict] = dspy.InputField(
        desc="Previously successful audit patterns from VectorStore",
        default_factory=list,
    )
    necessary_criteria: dict[str, float] = dspy.InputField(
        desc="NECESSARY pattern scoring criteria",
        default_factory=lambda: {
            "N": 0.8,  # No missing behaviors
            "E1": 0.7,  # Edge cases
            "C": 0.8,  # Comprehensive
            "E2": 0.7,  # Error conditions
            "S1": 0.9,  # State validation
            "S2": 0.9,  # Side effects
            "A": 0.6,  # Async operations
            "R": 0.8,  # Regression prevention
            "Y": 0.7,  # Yielding confidence
        },
    )

    # Outputs
    issues: list[Issue] = dspy.OutputField(
        desc="List of identified issues with severity and details"
    )
    qt_score: float = dspy.OutputField(desc="Overall quality score (0.0 to 1.0)")
    necessary_scores: dict[str, float] = dspy.OutputField(
        desc="Individual NECESSARY pattern scores"
    )
    recommendations: list[str] = dspy.OutputField(
        desc="Prioritized recommendations for improvement"
    )


class PrioritizationSignature(dspy.Signature):
    """Prioritize issues based on severity and impact."""

    # Inputs
    issues: list[Issue] = dspy.InputField(desc="All identified issues from audit")
    max_fixes: int = dspy.InputField(
        desc="Maximum number of fixes to attempt", default=3
    )
    priority_weights: dict[str, float] = dspy.InputField(
        desc="Weights for different issue categories",
        default_factory=lambda: {
            "constitutional": 0.5,
            "security": 0.3,
            "coverage": 0.15,
            "complexity": 0.05,
        },
    )
    available_time: int = dspy.InputField(
        desc="Available time in minutes for fixes", default=30
    )

    # Outputs
    prioritized_issues: list[Issue] = dspy.OutputField(desc="Issues sorted by priority")
    selected_issues: list[Issue] = dspy.OutputField(
        desc="Top issues selected for fixing"
    )
    rationale: str = dspy.OutputField(desc="Explanation of prioritization logic")


class RefactorSignature(dspy.Signature):
    """Generate refactoring plan for identified issues."""

    # Inputs
    issue: Issue = dspy.InputField(desc="Single issue to fix")
    codebase_context: dict = dspy.InputField(
        desc="AST analysis and dependency information"
    )
    historical_fixes: list[dict] = dspy.InputField(
        desc="Similar successful fixes from history", default_factory=list
    )
    constraints: dict[str, bool] = dspy.InputField(
        desc="Refactoring constraints",
        default_factory=lambda: {
            "preserve_api": True,
            "maintain_tests": True,
            "allow_new_deps": False,
        },
    )

    # Outputs
    refactoring_plan: RefactoringPlan = dspy.OutputField(
        desc="Detailed plan for fixing the issue"
    )
    alternative_approaches: list[str] = dspy.OutputField(
        desc="Alternative fix strategies if primary fails"
    )
    estimated_impact: dict[str, float] = dspy.OutputField(
        desc="Impact analysis: risk, benefit, time"
    )


class VerificationSignature(dspy.Signature):
    """Verify that fixes are successful and safe."""

    # Inputs
    original_state: dict = dspy.InputField(desc="Codebase state before fixes")
    applied_fixes: list[RefactoringPlan] = dspy.InputField(
        desc="Fixes that were applied"
    )
    test_results: dict[str, bool] = dspy.InputField(desc="Test execution results")
    performance_metrics: dict[str, float] = dspy.InputField(
        desc="Performance impact measurements", default_factory=dict
    )

    # Outputs
    success: bool = dspy.OutputField(desc="Whether all fixes were successful")
    failed_fixes: list[str] = dspy.OutputField(
        desc="List of fixes that failed verification"
    )
    rollback_needed: bool = dspy.OutputField(desc="Whether rollback is required")
    learned_patterns: list[dict] = dspy.OutputField(
        desc="Patterns to store for future learning"
    )
    final_qt_score: float = dspy.OutputField(desc="Q(T) score after all fixes")


class LearningSignature(dspy.Signature):
    """Extract learnings from audit and fix results."""

    # Inputs
    audit_result: dict = dspy.InputField(desc="Complete audit results")
    fix_results: list[dict] = dspy.InputField(desc="Results from applied fixes")
    execution_metrics: dict = dspy.InputField(desc="Performance and timing metrics")

    # Outputs
    success_patterns: list[dict] = dspy.OutputField(
        desc="Patterns that led to successful fixes"
    )
    failure_patterns: list[dict] = dspy.OutputField(desc="Anti-patterns to avoid")
    optimization_suggestions: list[str] = dspy.OutputField(
        desc="Suggestions for improving the audit process"
    )
    vectorstore_updates: list[tuple[str, dict]] = dspy.OutputField(
        desc="Key-value pairs to store in VectorStore"
    )
