"""
Type definitions for DSPy agents.

This module provides type-safe definitions to replace Dict[str, Any] usage
in compliance with Agency's constitutional requirement to avoid Any types.
"""

from typing import Literal, TypedDict, Union

from shared.type_definitions.json import JSONValue


class DSPyContext(TypedDict, total=False):
    """Type-safe context for DSPy operations."""

    repository_root: str
    current_task: str
    agent_name: str
    memory_store: object | None
    vector_store: object | None
    historical_patterns: list[dict[str, JSONValue]]
    quality_standards: list[str]
    constitutional_requirements: list[str]
    test_results: dict[str, JSONValue]
    implementation_notes: str
    error_details: list[str] | None
    metadata: dict[str, JSONValue]


class AgentContext(TypedDict, total=False):
    """Type-safe agent context."""

    agent_id: str
    agent_type: str
    capabilities: list[str]
    memory: object | None
    vector_store: object | None
    session_id: str | None


class TestResults(TypedDict, total=False):
    """Type-safe test results."""

    passed: int
    failed: int
    skipped: int
    errors: list[str]
    duration: float
    coverage: float | None


class ImplementationContext(TypedDict, total=False):
    """Type-safe implementation context."""

    files_modified: list[str]
    tests_added: list[str]
    dependencies_added: list[str]
    breaking_changes: bool
    migration_notes: str | None


class PlannerContext(TypedDict, total=False):
    """Type-safe planner context."""

    specification_path: str | None
    plan_type: Literal["feature", "bugfix", "refactor", "test"]
    priority: Literal["low", "medium", "high", "critical"]
    estimated_effort: str | None
    dependencies: list[str]
    risks: list[str]


class AuditContext(TypedDict, total=False):
    """Type-safe audit context."""

    target_paths: list[str]
    audit_type: Literal["security", "performance", "quality", "compliance"]
    severity_threshold: Literal["low", "medium", "high", "critical"]
    findings: list[dict[str, JSONValue]]
    recommendations: list[str]


class LearningContext(TypedDict, total=False):
    """Type-safe learning context."""

    patterns_learned: list[dict[str, JSONValue]]
    success_rate: float
    failure_reasons: list[str]
    improvements_suggested: list[str]
    knowledge_base_updated: bool


# Union type for all contexts
Context = Union[
    DSPyContext,
    AgentContext,
    TestResults,
    ImplementationContext,
    PlannerContext,
    AuditContext,
    LearningContext,
    dict[str, JSONValue],  # Fallback for compatibility (typed)
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
]
