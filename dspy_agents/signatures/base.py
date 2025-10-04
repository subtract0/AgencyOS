"""
Base DSPy Signatures for Agency Agents

Defines the core input/output specifications for agent tasks,
following the Agency's constitutional principles and quality standards.
"""

# Conditional DSPy import for gradual migration
try:
    import dspy

    DSPY_AVAILABLE = True
except ImportError:
    # Fallback for when DSPy is not yet installed
    class dspy:
        class Signature:
            def __init__(self):
                pass

        class InputField:
            def __init__(self, desc=None):
                self.desc = desc

        class OutputField:
            def __init__(self, desc=None):
                self.desc = desc

    DSPY_AVAILABLE = False


from pydantic import BaseModel, Field

from shared.type_definitions.json import JSONValue

# ===========================
# Data Models
# ===========================


class FileChange(BaseModel):
    """Represents a change to a file."""

    file_path: str = Field(..., description="Path to the file being modified")
    operation: str = Field(..., description="Operation: create, modify, delete")
    content: str | None = Field(None, description="New content for the file")
    diff: str | None = Field(None, description="Diff of changes for modify operations")


class TestSpecification(BaseModel):
    """Represents a test case."""

    test_file: str = Field(..., description="Path to test file")
    test_name: str = Field(..., description="Name of the test function")
    test_code: str = Field(..., description="Complete test implementation")
    follows_necessary: bool = Field(True, description="Whether test follows NECESSARY pattern")


class VerificationResult(BaseModel):
    """Result of verification checks."""

    all_tests_pass: bool = Field(..., description="Whether all tests pass")
    no_linting_errors: bool = Field(..., description="Whether there are no linting errors")
    constitutional_compliance: bool = Field(
        ..., description="Whether changes comply with constitution"
    )
    error_details: list[str] | None = Field(None, description="Details of any errors found")


class AgentResult(BaseModel):
    """Standard result from an agent operation."""

    success: bool = Field(..., description="Whether the operation succeeded")
    changes: list[FileChange] = Field(default_factory=list, description="File changes made")
    tests: list[TestSpecification] = Field(
        default_factory=list, description="Tests added or modified"
    )
    verification: VerificationResult | None = Field(None, description="Verification results")
    message: str | None = Field(None, description="Summary message")


class TaskPlan(BaseModel):
    """A plan for executing a task."""

    steps: list[str] = Field(..., description="Ordered list of steps to execute")
    agent_assignments: dict[str, str] = Field(
        default_factory=dict, description="Step to agent mapping"
    )
    estimated_time: int | None = Field(None, description="Estimated time in seconds")
    risk_factors: list[str] = Field(default_factory=list, description="Identified risks")


class AuditFinding(BaseModel):
    """A finding from code audit."""

    file_path: str = Field(..., description="File with the issue")
    line_number: int | None = Field(None, description="Line number of issue")
    severity: str = Field(..., description="Severity: critical, high, medium, low")
    category: str = Field(..., description="Category of issue")
    description: str = Field(..., description="Description of the finding")
    recommendation: str = Field(..., description="Recommended fix")


# ===========================
# Core Agent Signatures
# ===========================

if DSPY_AVAILABLE:

    class CodeTaskSignature(dspy.Signature):
        """Execute a code engineering task following Agency standards."""

        task_description: str = dspy.InputField(desc="The task to perform")
        context: dict[str, JSONValue] = dspy.InputField(desc="Repository and system context")
        historical_patterns: list[dict[str, JSONValue]] = dspy.InputField(
            desc="Previously successful patterns"
        )
        constitutional_requirements: list[str] = dspy.InputField(
            desc="Constitutional requirements to follow"
        )

        implementation_rationale: str = dspy.OutputField(
            desc="Step-by-step reasoning for the implementation approach, design decisions, and trade-offs considered"
        )
        code_changes: list[FileChange] = dspy.OutputField(desc="File modifications to make")
        tests_added: list[TestSpecification] = dspy.OutputField(desc="New or modified tests")
        verification_status: VerificationResult = dspy.OutputField(desc="Validation results")
        execution_plan: TaskPlan = dspy.OutputField(desc="How the task was executed")

    class PlanningSignature(dspy.Signature):
        """Create a detailed plan for a development task."""

        task: str = dspy.InputField(desc="Task to plan")
        context: dict[str, JSONValue] = dspy.InputField(desc="Current system state and context")
        constraints: list[str] = dspy.InputField(desc="Constraints and requirements")

        plan: TaskPlan = dspy.OutputField(desc="Detailed execution plan")
        rationale: str = dspy.OutputField(desc="Reasoning behind the plan")

    class ImplementationSignature(dspy.Signature):
        """Implement code changes based on a plan."""

        plan: TaskPlan = dspy.InputField(desc="Plan to implement")
        context: dict[str, JSONValue] = dspy.InputField(desc="Repository context")
        quality_standards: list[str] = dspy.InputField(desc="Quality standards to meet")

        decision_rationale: str = dspy.OutputField(
            desc="Reasoning behind implementation choices, alternatives considered, and why specific approaches were selected"
        )
        code_changes: list[FileChange] = dspy.OutputField(desc="Implemented changes")
        tests_added: list[TestSpecification] = dspy.OutputField(desc="Tests for the changes")
        implementation_notes: str = dspy.OutputField(desc="Notes about implementation decisions")

    class VerificationSignature(dspy.Signature):
        """Verify that implementation meets all requirements."""

        implementation: AgentResult = dspy.InputField(desc="Implementation to verify")
        test_results: dict[str, JSONValue] = dspy.InputField(desc="Results from running tests")
        constitutional_checks: list[str] = dspy.InputField(
            desc="Constitutional requirements to verify"
        )

        verification_rationale: str = dspy.OutputField(
            desc="Explanation of verification approach, checks performed, confidence assessment, and reasoning for pass/fail decisions"
        )
        verification_result: VerificationResult = dspy.OutputField(desc="Verification outcome")
        remediation_needed: list[str] = dspy.OutputField(desc="Issues that need fixing")

    # ===========================
    # Auditor Agent Signatures
    # ===========================

    class AuditSignature(dspy.Signature):
        """Analyze code for quality and compliance issues."""

        code_paths: list[str] = dspy.InputField(desc="Paths to analyze")
        audit_criteria: list[str] = dspy.InputField(desc="Criteria to audit against")
        necessary_patterns: dict[str, JSONValue] = dspy.InputField(
            desc="NECESSARY patterns to check"
        )

        audit_rationale: str = dspy.OutputField(
            desc="Reasoning behind audit findings, pattern detection logic, severity assessments, and compliance scoring methodology"
        )
        findings: list[AuditFinding] = dspy.OutputField(desc="Audit findings")
        compliance_score: float = dspy.OutputField(desc="Overall compliance score (0-1)")
        summary: str = dspy.OutputField(desc="Executive summary of audit")

    class PrioritizationSignature(dspy.Signature):
        """Prioritize findings or tasks based on impact."""

        items: list[dict[str, JSONValue]] = dspy.InputField(desc="Items to prioritize")
        criteria: list[str] = dspy.InputField(desc="Prioritization criteria")
        context: dict[str, JSONValue] = dspy.InputField(desc="Current system context")

        prioritized_items: list[dict[str, JSONValue]] = dspy.OutputField(
            desc="Items in priority order"
        )
        prioritization_rationale: str = dspy.OutputField(desc="Explanation of prioritization")

    class ReportSignature(dspy.Signature):
        """Generate a comprehensive report from analysis."""

        findings: list[AuditFinding] = dspy.InputField(desc="Findings to report")
        context: dict[str, JSONValue] = dspy.InputField(desc="Context for the report")
        report_format: str = dspy.InputField(desc="Format for report: markdown, json, html")

        report_rationale: str = dspy.OutputField(
            desc="Reasoning for report structure, metric selection, and prioritization of recommendations"
        )
        report: str = dspy.OutputField(desc="Generated report")
        key_metrics: dict[str, JSONValue] = dspy.OutputField(desc="Key metrics from analysis")
        recommendations: list[str] = dspy.OutputField(desc="Top recommendations")

    # ===========================
    # Planner Agent Signatures
    # ===========================

    class UnderstandingSignature(dspy.Signature):
        """Understand and analyze a feature request or task."""

        request: str = dspy.InputField(desc="User request or task description")
        existing_context: dict[str, JSONValue] = dspy.InputField(desc="Current system state")
        clarifying_questions: list[str] = dspy.InputField(desc="Questions to help understanding")

        understanding_rationale: str = dspy.OutputField(
            desc="Reasoning for interpretation, assumption derivation, and risk identification process"
        )
        understanding: str = dspy.OutputField(desc="Clear understanding of the request")
        assumptions: list[str] = dspy.OutputField(desc="Assumptions made")
        risks: list[str] = dspy.OutputField(desc="Identified risks")

    class StrategySignature(dspy.Signature):
        """Develop a strategy for implementing a feature."""

        understanding: str = dspy.InputField(desc="Understanding of the task")
        constraints: list[str] = dspy.InputField(desc="Technical and business constraints")
        available_resources: dict[str, JSONValue] = dspy.InputField(
            desc="Available agents and tools"
        )

        strategy_rationale: str = dspy.OutputField(
            desc="Reasoning for strategic approach, milestone selection, and success measurement methodology"
        )
        strategy: str = dspy.OutputField(desc="Implementation strategy")
        milestones: list[str] = dspy.OutputField(desc="Key milestones")
        success_criteria: list[str] = dspy.OutputField(desc="How to measure success")

    class TaskBreakdownSignature(dspy.Signature):
        """Break down a strategy into executable tasks."""

        strategy: str = dspy.InputField(desc="Strategy to break down")
        agent_capabilities: dict[str, list[str]] = dspy.InputField(desc="What each agent can do")
        dependencies: list[str] = dspy.InputField(desc="Task dependencies")

        breakdown_rationale: str = dspy.OutputField(
            desc="Reasoning for task decomposition, sequencing, agent assignments, and time estimates"
        )
        tasks: list[dict[str, JSONValue]] = dspy.OutputField(desc="Granular tasks")
        task_dependencies: dict[str, list[str]] = dspy.OutputField(desc="Task dependency graph")
        estimated_duration: int = dspy.OutputField(desc="Total estimated duration in seconds")

    # ===========================
    # Learning Agent Signatures
    # ===========================

    class PatternExtractionSignature(dspy.Signature):
        """Extract patterns from successful operations."""

        session_data: dict[str, JSONValue] = dspy.InputField(desc="Data from a session")
        pattern_types: list[str] = dspy.InputField(desc="Types of patterns to look for")
        minimum_confidence: float = dspy.InputField(desc="Minimum confidence threshold")

        extraction_rationale: str = dspy.OutputField(
            desc="Reasoning for pattern identification, confidence assessment, and extraction methodology"
        )
        patterns: list[dict[str, JSONValue]] = dspy.OutputField(desc="Extracted patterns")
        confidence_scores: dict[str, float] = dspy.OutputField(desc="Confidence in each pattern")

    class ConsolidationSignature(dspy.Signature):
        """Consolidate multiple patterns into learnings."""

        patterns: list[dict[str, JSONValue]] = dspy.InputField(desc="Patterns to consolidate")
        existing_knowledge: dict[str, JSONValue] = dspy.InputField(desc="Current knowledge base")
        validation_criteria: list[str] = dspy.InputField(desc="Criteria for valid learnings")

        consolidation_rationale: str = dspy.OutputField(
            desc="Reasoning for pattern consolidation, validation decisions, and knowledge integration approach"
        )
        consolidated_learnings: list[dict[str, JSONValue]] = dspy.OutputField(
            desc="Consolidated learnings"
        )
        knowledge_updates: dict[str, JSONValue] = dspy.OutputField(desc="Updates to knowledge base")
        validation_results: dict[str, bool] = dspy.OutputField(desc="Validation outcomes")

    class StorageSignature(dspy.Signature):
        """Store learnings in the knowledge base."""

        learnings: list[dict[str, JSONValue]] = dspy.InputField(desc="Learnings to store")
        storage_location: str = dspy.InputField(desc="Where to store: vectorstore, database, file")
        metadata: dict[str, JSONValue] = dspy.InputField(desc="Metadata for the learnings")

        storage_rationale: str = dspy.OutputField(
            desc="Reasoning for storage decisions, location selection, and metadata organization"
        )
        storage_confirmation: bool = dspy.OutputField(desc="Whether storage succeeded")
        storage_ids: list[str] = dspy.OutputField(desc="IDs of stored items")
        storage_summary: str = dspy.OutputField(desc="Summary of what was stored")

    # ===========================
    # Toolsmith Agent Signatures
    # ===========================

    class ToolDirectiveSignature(dspy.Signature):
        """Parse and understand a tool creation directive."""

        directive: str = dspy.InputField(desc="Tool creation directive")
        existing_tools: list[str] = dspy.InputField(desc="List of existing tools")
        constitutional_requirements: list[str] = dspy.InputField(desc="Constitutional requirements")

        design_rationale: str = dspy.OutputField(
            desc="Reasoning for tool design decisions, architectural choices, parameter selection, and integration considerations"
        )
        tool_name: str = dspy.OutputField(desc="Name of the tool to create")
        tool_description: str = dspy.OutputField(desc="Description of the tool's purpose")
        parameters: list[dict[str, JSONValue]] = dspy.OutputField(
            desc="Tool parameters specification"
        )
        test_cases: list[str] = dspy.OutputField(desc="Test cases to implement")
        implementation_plan: list[str] = dspy.OutputField(desc="Steps to implement the tool")

    class ToolScaffoldingSignature(dspy.Signature):
        """Scaffold a new tool following BaseTool patterns."""

        tool_name: str = dspy.InputField(desc="Name of the tool")
        tool_description: str = dspy.InputField(desc="Description of the tool")
        parameters: list[dict[str, JSONValue]] = dspy.InputField(desc="Tool parameters")
        base_patterns: dict[str, str] = dspy.InputField(
            desc="BaseTool and Pydantic patterns to follow"
        )

        scaffolding_rationale: str = dspy.OutputField(
            desc="Reasoning for code structure, pattern application, type choices, and implementation approach"
        )
        tool_code: str = dspy.OutputField(desc="Generated tool implementation")
        imports: list[str] = dspy.OutputField(desc="Required imports")
        docstring: str = dspy.OutputField(desc="Tool docstring")
        type_hints: dict[str, str] = dspy.OutputField(desc="Type hints for parameters")

    class TestGenerationSignature(dspy.Signature):
        """Generate comprehensive tests for a tool."""

        tool_name: str = dspy.InputField(desc="Name of the tool")
        tool_code: str = dspy.InputField(desc="Tool implementation code")
        test_requirements: list[str] = dspy.InputField(desc="Test requirements and cases")
        necessary_pattern: bool = dspy.InputField(desc="Whether to follow NECESSARY pattern")

        testing_rationale: str = dspy.OutputField(
            desc="Reasoning for test strategy, edge cases considered, coverage approach, and mock/fixture decisions"
        )
        test_code: str = dspy.OutputField(desc="Generated test code")
        test_fixtures: list[str] = dspy.OutputField(desc="Test fixtures and mocks")
        test_coverage: float = dspy.OutputField(desc="Estimated test coverage percentage")

    class HandoffSignature(dspy.Signature):
        """Prepare artifacts for handoff to MergerAgent."""

        artifacts: list[dict[str, JSONValue]] = dspy.InputField(
            desc="Created artifacts (tool, tests, etc)"
        )
        test_results: dict[str, JSONValue] = dspy.InputField(desc="Results from running tests")
        integration_notes: str = dspy.InputField(desc="Notes for integration")

        handoff_rationale: str = dspy.OutputField(
            desc="Reasoning for handoff readiness, integration recommendations, and risk assessment"
        )
        handoff_package: dict[str, JSONValue] = dspy.OutputField(desc="Package for MergerAgent")
        summary: str = dspy.OutputField(desc="Summary of created artifacts")
        next_steps: list[str] = dspy.OutputField(desc="Recommended next steps")

    # ===========================
    # Orchestrator Signatures
    # ===========================

    class TaskRoutingSignature(dspy.Signature):
        """Route a task to appropriate agent(s)."""

        request: str = dspy.InputField(desc="User request")
        available_agents: list[str] = dspy.InputField(desc="Available agents")
        agent_capabilities: dict[str, list[str]] = dspy.InputField(desc="What each agent can do")

        selected_agents: list[str] = dspy.OutputField(desc="Agents to use")
        routing_rationale: str = dspy.OutputField(desc="Why these agents were chosen")
        execution_order: list[str] = dspy.OutputField(desc="Order of agent execution")

    class CoordinationSignature(dspy.Signature):
        """Coordinate multi-agent execution."""

        agents: list[str] = dspy.InputField(desc="Agents to coordinate")
        task: str = dspy.InputField(desc="Task to accomplish")
        dependencies: dict[str, list[str]] = dspy.InputField(desc="Agent dependencies")

        coordination_rationale: str = dspy.OutputField(
            desc="Reasoning for coordination approach, communication patterns, and synchronization strategy"
        )
        coordination_plan: dict[str, JSONValue] = dspy.OutputField(
            desc="How agents will work together"
        )
        communication_protocol: dict[str, str] = dspy.OutputField(desc="How agents communicate")
        synchronization_points: list[str] = dspy.OutputField(desc="When to synchronize")

else:
    # Fallback signatures when DSPy is not available
    class CodeTaskSignature:
        """Fallback signature for code tasks."""

        pass

    class PlanningSignature:
        """Fallback signature for planning."""

        pass

    class ImplementationSignature:
        """Fallback signature for implementation."""

        pass

    class VerificationSignature:
        """Fallback signature for verification."""

        pass

    class AuditSignature:
        """Fallback signature for audit."""

        pass

    class PrioritizationSignature:
        """Fallback signature for prioritization."""

        pass

    class ReportSignature:
        """Fallback signature for report."""

        pass

    class UnderstandingSignature:
        """Fallback signature for understanding."""

        pass

    class StrategySignature:
        """Fallback signature for strategy."""

        pass

    class TaskBreakdownSignature:
        """Fallback signature for task breakdown."""

        pass

    class PatternExtractionSignature:
        """Fallback signature for pattern extraction."""

        pass

    class ConsolidationSignature:
        """Fallback signature for consolidation."""

        pass

    class StorageSignature:
        """Fallback signature for storage."""

        pass

    class ToolDirectiveSignature:
        """Fallback signature for tool directive."""

        pass

    class ToolScaffoldingSignature:
        """Fallback signature for tool scaffolding."""

        pass

    class TestGenerationSignature:
        """Fallback signature for test generation."""

        pass

    class HandoffSignature:
        """Fallback signature for handoff."""

        pass

    class TaskRoutingSignature:
        """Fallback signature for task routing."""

        pass

    class CoordinationSignature:
        """Fallback signature for coordination."""

        pass


# Export all signatures
__all__ = [
    "FileChange",
    "TestSpecification",
    "VerificationResult",
    "AgentResult",
    "TaskPlan",
    "AuditFinding",
    "CodeTaskSignature",
    "PlanningSignature",
    "ImplementationSignature",
    "VerificationSignature",
    "AuditSignature",
    "PrioritizationSignature",
    "ReportSignature",
    "UnderstandingSignature",
    "StrategySignature",
    "TaskBreakdownSignature",
    "PatternExtractionSignature",
    "ConsolidationSignature",
    "StorageSignature",
    "ToolDirectiveSignature",
    "ToolScaffoldingSignature",
    "TestGenerationSignature",
    "HandoffSignature",
    "TaskRoutingSignature",
    "CoordinationSignature",
]
