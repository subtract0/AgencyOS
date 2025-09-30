"""
Type definitions for DSPy agents.

This module provides type-safe definitions to replace Dict[str, Any] usage
in compliance with Agency's constitutional requirement to avoid Any types.
"""

from typing import TypedDict, Union, List, Optional, Literal
from pydantic import BaseModel


class DSPyContext(TypedDict, total=False):
    """Type-safe context for DSPy operations."""
    repository_root: str
    current_task: str
    agent_name: str
    memory_store: Optional[object]
    vector_store: Optional[object]
    historical_patterns: List[dict]
    quality_standards: List[str]
    constitutional_requirements: List[str]
    test_results: dict
    implementation_notes: str
    error_details: Optional[List[str]]
    metadata: dict


class AgentContext(TypedDict, total=False):
    """Type-safe agent context."""
    agent_id: str
    agent_type: str
    capabilities: List[str]
    memory: Optional[object]
    vector_store: Optional[object]
    session_id: Optional[str]


class TestResults(TypedDict, total=False):
    """Type-safe test results."""
    passed: int
    failed: int
    skipped: int
    errors: List[str]
    duration: float
    coverage: Optional[float]


class ImplementationContext(TypedDict, total=False):
    """Type-safe implementation context."""
    files_modified: List[str]
    tests_added: List[str]
    dependencies_added: List[str]
    breaking_changes: bool
    migration_notes: Optional[str]


class PlannerContext(TypedDict, total=False):
    """Type-safe planner context."""
    specification_path: Optional[str]
    plan_type: Literal["feature", "bugfix", "refactor", "test"]
    priority: Literal["low", "medium", "high", "critical"]
    estimated_effort: Optional[str]
    dependencies: List[str]
    risks: List[str]


class AuditContext(TypedDict, total=False):
    """Type-safe audit context."""
    target_paths: List[str]
    audit_type: Literal["security", "performance", "quality", "compliance"]
    severity_threshold: Literal["low", "medium", "high", "critical"]
    findings: List[dict]
    recommendations: List[str]


class LearningContext(TypedDict, total=False):
    """Type-safe learning context."""
    patterns_learned: List[dict]
    success_rate: float
    failure_reasons: List[str]
    improvements_suggested: List[str]
    knowledge_base_updated: bool


class AgentMetadata(TypedDict, total=False):
    """Type-safe agent metadata."""
    type: str
    version: str
    capabilities: List[str]
    status: str
    performance_score: float
    usage_count: int
    last_used: Optional[str]
    description: Optional[str]
    author: Optional[str]
    dependencies: List[str]


class PerformanceMetrics(TypedDict, total=False):
    """Type-safe performance metrics."""
    total_agents: int
    dspy_agents: int
    legacy_agents: int
    fallback_count: int
    agent_usage: dict
    average_performance: float


class TaskDict(TypedDict, total=False):
    """Type-safe task dictionary."""
    id: str
    name: str
    description: str
    status: str
    priority: int
    agent: Optional[str]
    dependencies: List[str]
    estimated_time: Optional[float]
    actual_time: Optional[float]
    result: Optional[str]


class PatternDict(TypedDict, total=False):
    """Type-safe pattern dictionary."""
    id: str
    type: str
    name: str
    description: str
    confidence: float
    frequency: int
    examples: List[str]
    metadata: dict


class ToolParameterDict(TypedDict, total=False):
    """Type-safe tool parameter dictionary."""
    name: str
    type: str
    description: str
    required: bool
    default: Optional[Union[str, int, float, bool]]


class ArtifactDict(TypedDict, total=False):
    """Type-safe artifact dictionary."""
    id: str
    type: str
    name: str
    path: str
    content: Optional[str]
    created_at: str
    metadata: dict


class HandoffPackageDict(TypedDict, total=False):
    """Type-safe handoff package dictionary."""
    artifacts: List[ArtifactDict]
    test_results: dict
    integration_notes: str
    summary: str
    next_steps: List[str]


class CoordinationPlanDict(TypedDict, total=False):
    """Type-safe coordination plan dictionary."""
    strategy: str
    agents: List[str]
    timeline: dict
    checkpoints: List[str]
    communication_protocol: dict


class ToolTestResults(TypedDict, total=False):
    """Type-safe tool test results."""
    passed: int
    failed: int
    test_names: List[str]
    error_messages: List[str]
    coverage: Optional[float]
    execution_time: float


class SuccessfulTool(TypedDict, total=False):
    """Type-safe successful tool record."""
    name: str
    path: str
    created_at: str
    test_status: str
    quality_score: float


class FailedAttempt(TypedDict, total=False):
    """Type-safe failed attempt record."""
    name: str
    error: str
    timestamp: str
    context: dict


class LearningMetrics(TypedDict, total=False):
    """Type-safe learning metrics."""
    successful_tools: List[dict]
    failed_attempts: List[dict]
    total_attempts: int
    success_rate: float
    common_failures: List[str]


class ToolDirective(TypedDict, total=False):
    """Type-safe tool directive."""
    name: str
    description: str
    parameters: List[ToolParameterDict]
    returns: str
    requirements: List[str]


class UserJourney(TypedDict, total=False):
    """Type-safe user journey."""
    name: str
    description: str
    steps: List[str]
    expected_outcome: str


class Architecture(TypedDict, total=False):
    """Type-safe architecture definition."""
    components: List[str]
    interactions: dict
    patterns: List[str]
    technologies: List[str]


class Contract(TypedDict, total=False):
    """Type-safe contract definition."""
    name: str
    type: str
    interface: dict
    validation: List[str]


class QualityStrategy(TypedDict, total=False):
    """Type-safe quality strategy."""
    testing_approach: str
    coverage_targets: dict
    validation_methods: List[str]
    acceptance_criteria: List[str]


class Risk(TypedDict, total=False):
    """Type-safe risk assessment."""
    type: str
    description: str
    likelihood: str
    impact: str
    mitigation: str


class Milestone(TypedDict, total=False):
    """Type-safe milestone."""
    name: str
    deliverables: List[str]
    deadline: Optional[str]
    dependencies: List[str]


class PlanningSummary(TypedDict, total=False):
    """Type-safe planning summary."""
    total_specs: int
    total_plans: int
    successful_implementations: int
    failed_attempts: int
    average_task_count: float
    planning_patterns: List[dict]


class SessionData(TypedDict, total=False):
    """Type-safe session data."""
    session_id: str
    start_time: str
    end_time: Optional[str]
    events: List[dict]
    metrics: dict


class Insight(TypedDict, total=False):
    """Type-safe insight."""
    type: str
    description: str
    confidence: float
    evidence: List[str]
    applications: List[str]


class LearningSummary(TypedDict, total=False):
    """Type-safe learning summary."""
    total_sessions: int
    patterns_extracted: int
    learnings_consolidated: int
    knowledge_updates: int
    confidence_average: float
    top_patterns: List[dict]


class SuccessPattern(TypedDict, total=False):
    """Type-safe success pattern."""
    task: str
    solution: str
    outcome: str
    confidence: float
    timestamp: str


class FailurePattern(TypedDict, total=False):
    """Type-safe failure pattern."""
    task: str
    error: str
    cause: str
    resolution: Optional[str]
    timestamp: str


class CodeLearning(TypedDict, total=False):
    """Type-safe code learning summary."""
    total_tasks: int
    success_rate: float
    common_task_types: dict
    success_patterns: List[dict]
    failure_patterns: List[dict]
    improvements_suggested: List[str]


# Union type for all contexts
Context = Union[
    DSPyContext,
    AgentContext,
    TestResults,
    ImplementationContext,
    PlannerContext,
    AuditContext,
    LearningContext,
    dict  # Fallback for compatibility
]


# Export all type definitions
__all__ = [
    "DSPyContext",
    "AgentContext",
    "TestResults",
    "ImplementationContext",
    "PlannerContext",
    "AuditContext",
    "LearningContext",
    "Context",
    "AgentMetadata",
    "PerformanceMetrics",
    "TaskDict",
    "PatternDict",
    "ToolParameterDict",
    "ArtifactDict",
    "HandoffPackageDict",
    "CoordinationPlanDict",
    "ToolTestResults",
    "SuccessfulTool",
    "FailedAttempt",
    "LearningMetrics",
    "ToolDirective",
    "UserJourney",
    "Architecture",
    "Contract",
    "QualityStrategy",
    "Risk",
    "Milestone",
    "PlanningSummary",
    "SessionData",
    "Insight",
    "LearningSummary",
    "SuccessPattern",
    "FailurePattern",
    "CodeLearning",
]